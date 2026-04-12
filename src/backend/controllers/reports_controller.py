"""Business logic for uploading medical reports to Supabase storage."""
import io
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image
from supabase import Client
from pdf2image import convert_from_bytes

from backend.extraction.gemini_extractor import extract_with_gemini
from backend.extraction.inserter import insert_lab_results, update_report_metadata
from backend.extraction.pipeline import process_report_with_gemini
from backend.ocr.preprocessor import preprocess_image
from backend.ocr.ocr_engine import run_ocr
from backend.services.reports_service import delete_report_and_related_alerts
from backend.services.retrieval.indexer import index_report

_log = logging.getLogger(__name__)


class ReportUploadError(RuntimeError):
    """Raised when a medical report cannot be uploaded."""


class ReportOCRError(RuntimeError):
    """Raised when OCR processing fails."""


def delete_report_for_user(report_id: str, user_id: str) -> dict:
    """Delete a report for a user, including related alerts."""
    if not report_id:
        raise ReportOCRError("report_id is required.")

    try:
        uuid.UUID(report_id)
    except ValueError as exc:
        raise ReportOCRError("report_id must be a valid UUID.") from exc

    return delete_report_and_related_alerts(report_id=report_id, user_id=user_id)

#Format the file name to ensure safety for storage paths.
def _sanitize_filename(filename: str) -> str:
    """Return a filesystem/storage-safe filename.

    Replaces characters that are unsafe for storage paths with an underscore.
    If the provided filename is empty or results in an empty string after
    sanitization, return the sensible default "report.pdf".
    """
    if not filename:
        return "report.pdf"
    # Replace characters that are unsafe for storage paths.
    base = re.sub(r"[^A-Za-z0-9._-]", "_", filename)
    return base or "report.pdf"

#Build a unique storage path for the uploaded report to avoid collisions and maintain user separation.
def build_report_path(
    user_id: str,
    original_filename: str,
    user_name: str | None = None,
) -> str:
    """Create a unique, user-scoped path for the uploaded report.

    Folder format:
      With name : ``FirstName_LastName_<user_id>/timestamp_uuid_filename``
      Without   : ``<user_id>/timestamp_uuid_filename``
    """
    safe_filename = _sanitize_filename(original_filename)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    unique_id = uuid.uuid4().hex
    if user_name:
        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", user_name.strip())
        folder = f"{safe_name}_{user_id}"
    else:
        folder = user_id
    return f"{folder}/{timestamp}_{unique_id}_{safe_filename}"


def upload_medical_report(
    client: Client,
    bucket: str,
    user_id: str,
    original_filename: str,
    file_bytes: bytes,
    content_type: str,
    user_name: str | None = None,
) -> Tuple[str, str]:
    """Upload raw file bytes to Supabase storage and return storage path and public URL.

    Validates inputs, creates a unique storage path for the user, uploads the
    bytes to the specified ``bucket``, and returns the storage path along with
    a public URL. Raises ``ReportUploadError`` on failure.

    The storage folder is named ``<user_name>_<user_id>/`` when *user_name* is
    provided, or just ``<user_id>/`` otherwise.
    """
    if not user_id:
        raise ReportUploadError("user_id is required for report uploads.")
    if not file_bytes:
        raise ReportUploadError("Uploaded file is empty.")

    # Build a unique storage path to keep reports separated by user and upload time.
    storage_path = build_report_path(user_id, original_filename, user_name=user_name)
    mime_type = content_type or "application/pdf"

    try:
        # Upload the bytes to Supabase Storage with the detected MIME type.
        client.storage.from_(bucket).upload(
            storage_path,
            file_bytes,
            {
                "content-type": mime_type,
                "upsert": False,
            },
        )
        # Resolve a public URL for the newly uploaded report.
        public_url = client.storage.from_(bucket).get_public_url(storage_path)
    except Exception as exc:  # supabase-py raises generic exceptions from storage operations
        raise ReportUploadError(f"Failed to upload report: {exc}") from exc

    return storage_path, public_url


def _pdf_to_images(pdf_bytes: bytes) -> List[Image.Image]:
    """Convert PDF bytes to a list of PIL images (one per page)."""
    return convert_from_bytes(pdf_bytes)


def _image_bytes_to_pil(image_bytes: bytes) -> Image.Image:
    """Decode raw image bytes into a PIL Image."""
    img = Image.open(io.BytesIO(image_bytes))
    img.load()  # Force read so the BytesIO can be GC'd
    return img


def _tesseract_extract_text(images: List[Image.Image]) -> Tuple[str, float]:
    """Extract text from report page images using Tesseract OCR.

    Converts each PIL Image to a preprocessed NumPy array, runs Tesseract,
    and concatenates the per-page text with ``--- Page N ---`` markers.

    Returns
    -------
    tuple[str, float]
        ``(full_ocr_text, avg_confidence)`` where confidence is 0-100.
    """
    page_texts: List[str] = []
    confidences: List[float] = []

    for page_num, pil_img in enumerate(images, start=1):
        # Convert PIL Image → BGR NumPy array for OpenCV preprocessing
        img_array = np.array(pil_img.convert("RGB"))[..., ::-1]  # RGB → BGR
        preprocessed = preprocess_image(img_array)
        text, conf = run_ocr(preprocessed)
        page_texts.append(f"--- Page {page_num} ---\n{text}")
        if conf >= 0:
            confidences.append(conf)
        _log.info(
            "Tesseract OCR page %d/%d: %d chars, confidence=%.1f%%",
            page_num, len(images), len(text), conf,
        )

    full_text = "\n\n".join(page_texts)
    avg_confidence = float(sum(confidences) / len(confidences)) if confidences else 0.0
    return full_text, avg_confidence


def run_ocr_on_report(
    client: Client,
    bucket: str,
    table: str,
    user_id: str,
    storage_path: str,
) -> Tuple[str, float, str]:
    """Download a stored report, run Tesseract OCR, persist the result, and index.

    Uses Tesseract (via the ``ocr`` module) for text extraction.  This is the
    standalone OCR step for the ``POST /reports/ocr`` endpoint — Gemini lab
    extraction is a separate subsequent step.

    Returns a tuple of (extracted_text, avg_confidence, report_id).
    """
    if not user_id:
        raise ReportOCRError("user_id is required for OCR.")
    if not storage_path:
        raise ReportOCRError("storage_path is required for OCR.")

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError as exc:
        raise ReportOCRError("user_id must be a valid UUID.") from exc

    try:
        report_bytes = client.storage.from_(bucket).download(storage_path)
    except Exception as exc:
        raise ReportOCRError(f"Failed to download report: {exc}") from exc

    try:
        if storage_path.lower().endswith(".pdf"):
            images = _pdf_to_images(report_bytes)
        else:
            images = [_image_bytes_to_pil(report_bytes)]
        text, confidence = _tesseract_extract_text(images)
    except Exception as exc:
        raise ReportOCRError(f"Tesseract OCR failed: {exc}") from exc

    try:
        public_url = client.storage.from_(bucket).get_public_url(storage_path)
        source_file_name = os.path.basename(storage_path)
        report_id = str(uuid.uuid4())
        client.table(table).insert(
            {
                "id": report_id,
                "user_id": str(user_uuid),
                "source_file_name": source_file_name,
                "source_url": public_url,
                "storage_path": storage_path,
                "ocr_text": text,
                "ocr_engine": "tesseract",
                "ocr_confidence": confidence,
            }
        ).execute()
    except Exception as exc:
        raise ReportOCRError(f"Failed to store OCR result: {exc}") from exc

    # Auto-index chunks for RAG retrieval (best-effort).
    try:
        n = index_report(
            report_id=report_id,
            user_id=str(user_uuid),
            ocr_text=text,
            source_filename=source_file_name,
            source_url=public_url,
            report_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        )
        _log.info("Auto-indexed %d chunks for report_id=%s", n, report_id)
    except Exception as exc:  # noqa: BLE001
        _log.warning(
            "Chunk indexing failed for report_id=%s (non-fatal): %s",
            report_id, exc,
        )

    return text, confidence, report_id


def extract_labs_for_report(
    client: Client,
    report_id: str,
) -> int:
    """Fetch OCR text for a report and extract lab results using Gemini.

    Delegates to :func:`extract_labs_with_gemini` which uses Gemini AI
    for extraction instead of the legacy regex pipeline.
    """
    result = extract_labs_with_gemini(client=client, report_id=report_id)
    return result.get("inserted", 0)


def extract_labs_with_gemini(
    client: Client,
    report_id: str,
) -> dict:
    """Extract lab results using Gemini AI and insert into lab_results.

    This replaces the regex-based extraction with LLM intelligence for
    superior handling of OCR noise and varied report formats.
    """
    if not report_id:
        raise ReportOCRError("report_id is required.")

    try:
        uuid.UUID(report_id)
    except ValueError as exc:
        raise ReportOCRError("report_id must be a valid UUID.") from exc

    return process_report_with_gemini(client=client, report_id=report_id)


# ---------------------------------------------------------------------------
# Async pipeline helpers (used by POST /reports/ingest)
# ---------------------------------------------------------------------------

def create_pending_report(
    client: Client,
    table: str,
    user_id: str,
    storage_path: str,
    public_url: str,
    source_file_name: str,
) -> str:
    """Insert a placeholder row in *table* with processing_status='pending'.

    This is called synchronously before returning 202 to the client so the
    caller immediately has a ``report_id`` to poll.  OCR text is left NULL
    (requires migration 003 which makes the column nullable).

    Returns the new ``report_id`` UUID string.
    """
    report_id = str(uuid.uuid4())
    # Try inserting with processing_status + nullable ocr_text (requires migration 003).
    # If the column doesn't exist yet (PGRST204), fall back to a plain insert that
    # works with the original schema (ocr_text NOT NULL, no processing_status).
    for attempt in range(2):
        try:
            payload: dict = {
                "id": report_id,
                "user_id": user_id,
                "source_file_name": source_file_name,
                "source_url": public_url,
            }
            if attempt == 0:
                # Full payload — needs migration 003
                payload["ocr_text"] = None
                payload["processing_status"] = "pending"
                payload["storage_path"] = storage_path
            else:
                # Fallback — original schema (ocr_text NOT NULL, no status col)
                payload["ocr_text"] = ""
            client.table(table).insert(payload).execute()
            return report_id
        except Exception as exc:
            exc_str = str(exc)
            if attempt == 0 and "PGRST204" in exc_str:
                _log.warning(
                    "processing_status column missing (migration 003 not applied) — "
                    "falling back to legacy insert for report_id=%s",
                    report_id,
                )
                continue
            raise ReportUploadError(f"Failed to create pending report row: {exc}") from exc
    return report_id  # unreachable, satisfies type checkers


def _update_report_status(
    client: Client,
    table: str,
    report_id: str,
    status: str,
    error: Optional[str] = None,
    extra: Optional[dict] = None,
) -> None:
    """Patch the processing_status (and optionally other fields) on a report row.

    If the ``processing_status`` column doesn't exist (migration 003 not yet
    applied), falls back to updating only the ``extra`` fields (e.g. ``ocr_text``,
    ``ocr_confidence``) so OCR results are still persisted.
    """
    payload: dict = {"processing_status": status}
    if error is not None:
        payload["processing_error"] = error
    if extra:
        payload.update(extra)
    try:
        client.table(table).update(payload).eq("id", report_id).execute()
        return
    except Exception as exc:  # noqa: BLE001 — status updates are best-effort
        if "PGRST204" in str(exc) and extra:
            # Column missing — retry with only the extra fields (e.g. ocr_text)
            try:
                client.table(table).update(extra).eq("id", report_id).execute()
                return
            except Exception:  # noqa: BLE001
                pass
        _log.warning("Could not update status for report_id=%s: %s", report_id, exc)


def run_full_pipeline_background(
    client: Client,
    bucket: str,
    table: str,
    user_id: str,
    storage_path: str,
    report_id: str,
) -> None:
    """Run Tesseract OCR → Gemini lab extraction on a pre-created pending report row.

    Designed to be called as a FastAPI ``BackgroundTask`` so it executes
    **after** the HTTP 202 response has been sent.

    Pipeline:
        1. Download report bytes from Supabase Storage.
        2. Convert to images.
        3. **Tesseract OCR** — extract raw text from all pages.
        4. Update the ``medical_reports`` row with OCR text, set status ``ocr_complete``.
        5. **Gemini** — parse the OCR text into structured lab results.
        6. Insert lab results + update report metadata.
        7. Auto-index chunks for RAG retrieval (best-effort).
        8. Mark status as ``done`` (or ``failed`` on any error).
    """
    _log.info("Background pipeline started for report_id=%s", report_id)

    # ── Stage 1 — Download ────────────────────────────────────────────────────
    try:
        report_bytes = client.storage.from_(bucket).download(storage_path)
    except Exception as exc:
        msg = f"Storage download failed: {exc}"
        _log.error("report_id=%s — %s", report_id, msg)
        _update_report_status(client, table, report_id, "failed", error=msg)
        return

    # ── Stage 2 — Convert to images ───────────────────────────────────────────
    try:
        if storage_path.lower().endswith(".pdf"):
            images = _pdf_to_images(report_bytes)
        else:
            images = [_image_bytes_to_pil(report_bytes)]
    except Exception as exc:
        msg = f"Image conversion failed: {exc}"
        _log.error("report_id=%s — %s", report_id, msg)
        _update_report_status(client, table, report_id, "failed", error=msg)
        return

    # ── Stage 3 — Tesseract OCR ───────────────────────────────────────────────
    try:
        ocr_text, ocr_confidence = _tesseract_extract_text(images)
    except Exception as exc:
        msg = f"Tesseract OCR failed: {exc}"
        _log.error("report_id=%s — %s", report_id, msg)
        _update_report_status(client, table, report_id, "failed", error=msg)
        return

    _log.info(
        "Tesseract OCR complete for report_id=%s (text_len=%d, confidence=%.1f%%)",
        report_id, len(ocr_text), ocr_confidence,
    )

    # ── Stage 4 — Persist OCR text ────────────────────────────────────────────
    _update_report_status(
        client, table, report_id, "ocr_complete",
        extra={
            "ocr_text": ocr_text,
            "ocr_engine": "tesseract",
            "ocr_confidence": ocr_confidence,
        },
    )

    if not ocr_text.strip():
        _log.warning("report_id=%s — Tesseract returned empty text; skipping Gemini extraction.", report_id)
        _update_report_status(client, table, report_id, "done")
        return

    # ── Stage 5 — Gemini lab result extraction from OCR text ──────────────────
    try:
        gemini_result = extract_with_gemini(ocr_text)
    except Exception as exc:
        msg = f"Gemini lab extraction failed: {exc}"
        _log.error("report_id=%s — %s", report_id, msg)
        _update_report_status(client, table, report_id, "failed", error=msg)
        return

    _log.info(
        "Gemini extraction complete for report_id=%s — %d lab results found",
        report_id, len(gemini_result.lab_results),
    )

    # ── Stage 6 — Insert lab results ──────────────────────────────────────────
    try:
        inserted, skipped, reasons = insert_lab_results(
            client=client,
            report_id=report_id,
            lab_results=gemini_result.lab_results,
        )
        _log.info(
            "Inserted %d lab results (%d skipped) for report_id=%s",
            inserted, skipped, report_id,
        )
        update_report_metadata(
            client=client,
            report_id=report_id,
            metadata=gemini_result.metadata,
        )
    except Exception as exc:
        msg = f"Lab results insertion failed: {exc}"
        _log.error("report_id=%s — %s", report_id, msg)
        _update_report_status(client, table, report_id, "failed", error=msg)
        return

    # ── Stage 7 — RAG indexing (best-effort, non-fatal) ───────────────────────
    source_file_name = os.path.basename(storage_path)
    public_url = client.storage.from_(bucket).get_public_url(storage_path)
    try:
        n = index_report(
            report_id=report_id,
            user_id=user_id,
            ocr_text=ocr_text,
            source_filename=source_file_name,
            source_url=public_url,
            report_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        )
        _log.info("Auto-indexed %d chunks for report_id=%s", n, report_id)
    except Exception as exc:  # noqa: BLE001
        _log.warning(
            "Chunk indexing failed for report_id=%s (non-fatal): %s",
            report_id, exc,
        )

    _update_report_status(client, table, report_id, "done")
    _log.info("Pipeline complete for report_id=%s", report_id)


def run_full_pipeline_sync(
    client: Client,
    table: str,
    user_id: str,
    file_bytes: bytes,
    original_filename: str,
    storage_path: str,
    public_url: str,
) -> dict:
    """Run the full extraction pipeline synchronously.

    Step 1: Tesseract OCR — extract raw text from all report pages.
    Step 2: Gemini AI — parse OCR text into structured lab results.

    Used by the ``POST /reports/process`` synchronous endpoint.
    Returns a dict with report_id, ocr_text_preview, inserted count, etc.
    """
    # Convert to images
    if original_filename.lower().endswith(".pdf"):
        images = _pdf_to_images(file_bytes)
    else:
        images = [_image_bytes_to_pil(file_bytes)]

    # Step 1 — Tesseract OCR
    ocr_text, ocr_confidence = _tesseract_extract_text(images)

    # Step 2 — Gemini extracts structured lab results from OCR text
    gemini_result = extract_with_gemini(ocr_text) if ocr_text.strip() else None

    # Create DB row with OCR results
    source_file_name = os.path.basename(storage_path)
    report_id = str(uuid.uuid4())
    try:
        client.table(table).insert(
            {
                "id": report_id,
                "user_id": user_id,
                "source_file_name": source_file_name,
                "source_url": public_url,
                "storage_path": storage_path,
                "ocr_text": ocr_text,
                "ocr_engine": "tesseract",
                "ocr_confidence": ocr_confidence,
                "processing_status": "ocr_complete" if ocr_text.strip() else "done",
            }
        ).execute()
    except Exception as exc:
        raise ReportOCRError(f"Failed to create report row: {exc}") from exc

    inserted = 0
    skipped = 0
    metadata_updates: dict = {}

    if gemini_result is not None:
        # Insert lab results from Gemini
        inserted, skipped, skip_reasons = insert_lab_results(
            client=client,
            report_id=report_id,
            lab_results=gemini_result.lab_results,
        )
        metadata_updates = update_report_metadata(
            client=client,
            report_id=report_id,
            metadata=gemini_result.metadata,
        )
        # Mark done
        try:
            client.table(table).update({"processing_status": "done"}).eq("id", report_id).execute()
        except Exception:  # noqa: BLE001
            pass

    # RAG indexing (best-effort)
    if ocr_text.strip():
        try:
            index_report(
                report_id=report_id,
                user_id=user_id,
                ocr_text=ocr_text,
                source_filename=source_file_name,
                source_url=public_url,
                report_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            )
        except Exception:  # noqa: BLE001
            pass

    return {
        "report_id": report_id,
        "ocr_text_preview": ocr_text[:500],
        "ocr_confidence": ocr_confidence,
        "inserted": inserted,
        "skipped": skipped,
        "metadata_updates": metadata_updates,
        "gemini_notes": gemini_result.extraction_notes if gemini_result else None,
    }
