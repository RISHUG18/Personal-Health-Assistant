"""Business logic for uploading medical reports to Supabase storage."""
import io
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image
from supabase import Client
from pdf2image import convert_from_bytes

from backend.extraction.gemini_extractor import extract_from_images_with_gemini
from backend.extraction.inserter import insert_lab_results, update_report_metadata
from backend.extraction.pipeline import process_report_with_gemini
from backend.services.retrieval.indexer import index_report

_log = logging.getLogger(__name__)

# ── File-based extraction log ──────────────────────────────────────────────────
# Appends a human-readable entry to extraction.log after every pipeline run so
# you can inspect exactly what Gemini returned and whether it hit the DB.
_EXTRACTION_LOG = Path(__file__).resolve().parent.parent.parent / "extraction.log"


def _log_extraction(
    report_id: str,
    filename: str,
    ocr_text: str,
    gemini_result=None,
    inserted: int = 0,
    skipped: int = 0,
    skip_reasons: list | None = None,
    error: str | None = None,
) -> None:
    """Append a structured extraction entry to extraction.log."""
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        sep = "=" * 70
        lines = [
            sep,
            f"EXTRACTION LOG — {now}",
            f"report_id : {report_id}",
            f"filename  : {filename}",
            f"ocr_len   : {len(ocr_text)} chars",
        ]
        if error:
            lines.append(f"ERROR     : {error}")
        elif gemini_result is not None:
            meta = gemini_result.metadata
            lines += [
                f"date      : {meta.report_date}",
                f"type      : {meta.report_type}",
                f"patient   : {meta.patient_name}",
                f"lab       : {meta.lab_name}",
                f"extracted : {len(gemini_result.lab_results)} results",
                f"inserted  : {inserted}  |  skipped: {skipped}",
            ]
            if skip_reasons:
                for r in skip_reasons:
                    lines.append(f"  skip > {r}")
            lines.append("--- Lab Results ---")
            for i, lr in enumerate(gemini_result.lab_results, 1):
                val = lr.value if lr.value is not None else lr.value_string or "N/A"
                lines.append(
                    f"  [{i:02}] {lr.test_name:<40} = {val} {lr.unit or ''}  "
                    f"(ref: {lr.reference_range or '—'}, "
                    f"abnormal: {lr.is_abnormal}, page: {lr.page_number})"
                )
        lines.append(sep)
        with open(_EXTRACTION_LOG, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    except Exception as exc:  # noqa: BLE001
        _log.warning("Could not write to extraction.log: %s", exc)



class ReportUploadError(RuntimeError):
    """Raised when a medical report cannot be uploaded."""


class ReportOCRError(RuntimeError):
    """Raised when OCR processing fails."""

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
    import shutil
    # Explicitly resolve poppler path so it works even when Uvicorn runs
    # in a restricted shell that doesn't inherit the full system PATH.
    poppler_path = None
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm:
        poppler_path = os.path.dirname(pdftoppm)  # e.g. /usr/bin
    return convert_from_bytes(pdf_bytes, poppler_path=poppler_path)



def _image_bytes_to_pil(image_bytes: bytes) -> Image.Image:
    """Decode raw image bytes into a PIL Image."""
    img = Image.open(io.BytesIO(image_bytes))
    img.load()  # Force read so the BytesIO can be GC'd
    return img


def _gemini_extract_text(images: List[Image.Image]) -> str:
    """Use Gemini vision to extract text from report page images.

    This is a lightweight OCR-only call — it does not extract structured
    lab results.  Used by the standalone ``/reports/ocr`` endpoint.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ReportOCRError("GEMINI_API_KEY is not set.")

    from google import genai
    from google.genai import types as genai_types

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    client = genai.Client(api_key=api_key)

    contents: list = list(images)
    contents.append(
        "Extract ALL text from these medical report page images. "
        "Return the complete text preserving the original structure, "
        "line breaks, and formatting. Return ONLY the extracted text, "
        "no additional commentary or markup."
    )

    response = client.models.generate_content(
        model=model_name,
        contents=contents,
        config=genai_types.GenerateContentConfig(temperature=0.1),
    )
    return (response.text or "").strip()


def run_ocr_on_report(
    client: Client,
    bucket: str,
    table: str,
    user_id: str,
    storage_path: str,
) -> Tuple[str, float, str]:
    """Download a stored report, extract text using Gemini vision, persist, and index.

    Uses Gemini's multimodal vision to read text directly from report images,
    bypassing Tesseract OCR for higher accuracy on tabular lab data.

    Returns a tuple of (extracted_text, confidence, report_id).
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
        text = _gemini_extract_text(images)
    except Exception as exc:
        raise ReportOCRError(f"Text extraction failed: {exc}") from exc

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
                "ocr_text": text,
                "ocr_engine": "gemini",
            }
        ).execute()
    except Exception as exc:
        raise ReportOCRError(f"Failed to store result: {exc}") from exc

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

    return text, 100.0, report_id


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
        exc_str = str(exc)
        if "PGRST204" in exc_str:
            # Fallback 1: Retain other fields but drop processing_error
            if error is not None:
                try:
                    fallback = {k: v for k, v in payload.items() if k != "processing_error"}
                    client.table(table).update(fallback).eq("id", report_id).execute()
                    return
                except Exception as fallback_exc:
                    exc_str = str(fallback_exc)
                    
            # Fallback 2: Retry with only the extra fields (e.g. ocr_text)
            if "PGRST204" in exc_str and extra:
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
    """Run Gemini vision extraction on a pre-created pending report row.

    Designed to be called as a FastAPI ``BackgroundTask`` so it executes
    **after** the HTTP 202 response has been sent.

    Pipeline:
        1. Download report bytes from Supabase Storage.
        2. Convert to images and send directly to Gemini for extraction.
        3. Update the ``medical_reports`` row with extracted text.
        4. Insert lab results from Gemini structured output.
        5. Auto-index chunks for RAG retrieval (best-effort).
        6. Mark status as ``done`` (or ``failed`` on any error).
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

    # ── Stage 3 — Run Tesseract OCR on images ───────────────
    try:
        from backend.ocr.preprocessor import preprocess_image
        from backend.ocr.ocr_engine import run_ocr
        import numpy as np

        text_parts = []
        for img in images:
            # Convert PIL image to OpenCV BGR format needed by preprocessor
            open_cv_image = np.array(img)
            image_bgr = open_cv_image[:, :, ::-1].copy()
            
            processed = preprocess_image(image_bgr)
            page_text, _conf = run_ocr(processed)
            text_parts.append(page_text)
            
        ocr_text = "\n\n".join(text_parts).strip()
    except Exception as exc:
        msg = f"Tesseract OCR failed: {exc}"
        _log.error("report_id=%s — %s", report_id, msg)
        _update_report_status(client, table, report_id, "failed", error=msg)
        return

    # ── Stage 4 — Update DB with extracted text ───────────────────────────────
    _update_report_status(
        client, table, report_id, "ocr_complete",
        extra={"ocr_text": ocr_text, "ocr_engine": "tesseract"},
    )
    _log.info(
        "Tesseract OCR complete for report_id=%s (text_len=%d)",
        report_id, len(ocr_text),
    )

    # ── Stage 4.5 — Structured Extraction with Gemini text model ──────────────
    _source_filename = os.path.basename(storage_path)
    try:
        from backend.extraction.gemini_extractor import extract_with_gemini
        gemini_result = extract_with_gemini(ocr_text)
    except Exception as exc:
        msg = f"Gemini structured extraction failed: {exc}"
        _log.error("report_id=%s — %s", report_id, msg)
        _log_extraction(report_id, _source_filename, ocr_text, error=msg)
        _update_report_status(client, table, report_id, "failed", error=msg)
        return

    _log.info(
        "Gemini extraction complete for report_id=%s (%d lab results)",
        report_id, len(gemini_result.lab_results),
    )

    # ── Stage 5 — Insert lab results ──────────────────────────────────────────
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
        # Write human-readable extraction record to extraction.log
        _log_extraction(
            report_id, _source_filename, ocr_text,
            gemini_result=gemini_result,
            inserted=inserted,
            skipped=skipped,
            skip_reasons=reasons,
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

    # ── Stage 6 — RAG indexing (best-effort, non-fatal) ───────────────────────
    if ocr_text.strip():
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

    # ── Stage 7 — Auto-evaluate alerts (best-effort, non-fatal) ──────────────
    try:
        from backend.rules.engine import evaluate_rules
        from backend.rules.inserter import persist_alerts
        alerts = evaluate_rules(client=client, user_id=user_id)
        result = persist_alerts(client=client, user_id=user_id, alerts=alerts)
        _log.info(
            "Auto-alert evaluation for user_id=%s: %d triggered, %d inserted, %d evidence rows",
            user_id, len(alerts), result.get("inserted", 0), result.get("evidence_inserted", 0),
        )
    except Exception as exc:  # noqa: BLE001
        _log.warning("Auto-alert evaluation failed for user_id=%s (non-fatal): %s", user_id, exc)



def run_full_pipeline_sync(
    client: Client,
    table: str,
    user_id: str,
    file_bytes: bytes,
    original_filename: str,
    storage_path: str,
    public_url: str,
) -> dict:
    """Run the full extraction pipeline synchronously using Gemini vision.

    Converts the report to images and sends them directly to Gemini in a
    single API call for both text extraction and structured lab data extraction.
    Used by the ``POST /reports/process`` synchronous endpoint.

    Returns a dict with report_id, ocr_text_preview, inserted count, etc.
    """
    # Convert to images
    if original_filename.lower().endswith(".pdf"):
        images = _pdf_to_images(file_bytes)
    else:
        images = [_image_bytes_to_pil(file_bytes)]

    # Run Tesseract OCR on images
    from backend.ocr.preprocessor import preprocess_image
    from backend.ocr.ocr_engine import run_ocr
    import numpy as np

    text_parts = []
    for img in images:
        open_cv_image = np.array(img)
        image_bgr = open_cv_image[:, :, ::-1].copy()
        processed = preprocess_image(image_bgr)
        page_text, _conf = run_ocr(processed)
        text_parts.append(page_text)
        
    ocr_text = "\n\n".join(text_parts).strip()

    # Create DB row
    source_file_name = os.path.basename(storage_path)
    report_id = str(uuid.uuid4())
    try:
        client.table(table).insert(
            {
                "id": report_id,
                "user_id": user_id,
                "source_file_name": source_file_name,
                "source_url": public_url,
                "ocr_text": ocr_text,
                "ocr_engine": "tesseract",
            }
        ).execute()
    except Exception as exc:
        raise ReportOCRError(f"Failed to create report row: {exc}") from exc

    # Structured extraction with Gemini
    from backend.extraction.gemini_extractor import extract_with_gemini
    gemini_result = extract_with_gemini(ocr_text)

    # Insert lab results
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

    # RAG indexing (best-effort)
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
        "inserted": inserted,
        "skipped": skipped,
        "metadata_updates": metadata_updates,
        "gemini_notes": gemini_result.extraction_notes,
    }
