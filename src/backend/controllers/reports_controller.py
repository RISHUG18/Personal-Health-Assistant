"""Business logic for uploading medical reports to Supabase storage."""
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

from supabase import Client
import pytesseract

import cv2
import numpy as np
from pdf2image import convert_from_bytes

from backend.ocr.preprocessor import preprocess_image
from backend.ocr.ocr_engine import run_ocr
from backend.ocr.pipeline import process_report_ocr
from backend.extraction.pipeline import process_report_with_gemini
from backend.services.retrieval.indexer import index_report

_log = logging.getLogger(__name__)


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


def _extract_text_from_pdf(pdf_bytes: bytes) -> tuple[str, float]:
    """Convert PDF bytes to images, run OCR per page, and return combined text.

    This function converts each PDF page to a PIL image, converts to an OpenCV
    array for preprocessing, runs OCR on each page, concatenates the
    per-page text with simple page separators, and returns the aggregated
    text along with the average OCR confidence across pages.
    """
    full_text = ""
    total_confidence = 0.0
    page_count = 0

    pages = convert_from_bytes(pdf_bytes)
    for i, pil_image in enumerate(pages):
        # Convert PIL -> OpenCV (BGR) and run preprocessing & OCR.
        open_cv_image = np.array(pil_image)
        image = open_cv_image[:, :, ::-1].copy()
        processed = preprocess_image(image)
        text, confidence = run_ocr(processed)
        full_text += f"\n--- Page {i + 1} ---\n{text}"
        total_confidence += confidence
        page_count += 1

    avg_confidence = total_confidence / page_count if page_count > 0 else 0.0
    return full_text.strip(), avg_confidence


def _extract_text_from_image(image_bytes: bytes) -> tuple[str, float]:
    """Decode raw image bytes, preprocess, and run OCR.

    Returns a tuple of (text, confidence). Raises `ReportOCRError` if the
    bytes cannot be decoded into an image.
    """
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ReportOCRError("Could not decode image bytes.")
    processed = preprocess_image(image)
    return run_ocr(processed)


def run_ocr_on_report(
    client: Client,
    bucket: str,
    table: str,
    user_id: str,
    storage_path: str,
) -> Tuple[str, float, str]:
    """Download a stored report, run OCR, persist the OCR results, and index.

    Steps performed:
    - Validate `user_id` and `storage_path` inputs.
    - Download the raw report bytes from Supabase storage.
    - If a PDF, convert pages and OCR each page; otherwise decode image bytes.
    - Persist a new record in `table` (typically `medical_reports`) with OCR
      text and metadata.
    - Attempt to auto-index the report into the retrieval index (best-effort).

    Returns a tuple of (ocr_text, avg_confidence, report_id).
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
        # Download the stored report bytes from Supabase storage.
        report_bytes = client.storage.from_(bucket).download(storage_path)
    except Exception as exc:
        raise ReportOCRError(f"Failed to download report: {exc}") from exc

    try:
        # Choose PDF or image extraction path based on filename extension.
        if storage_path.lower().endswith(".pdf"):
            text, confidence = _extract_text_from_pdf(report_bytes)
        else:
            text, confidence = _extract_text_from_image(report_bytes)
    except Exception as exc:
        raise ReportOCRError(f"OCR processing failed: {exc}") from exc

    try:
        # Persist the OCR result into the `medical_reports` table (or provided table).
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
                "ocr_engine": "tesseract",
                "ocr_confidence": confidence,
            }
        ).execute()
    except Exception as exc:
        raise ReportOCRError(f"Failed to store OCR result: {exc}") from exc

    # Auto-index chunks for RAG retrieval. This is best-effort and should not
    # cause the OCR API to fail if indexing has an error.
    # Week-3 RAG ingestion improvement — pass source_filename and report_date
    # so that chunk metadata is as complete as possible at indexing time.
    _log.info(
        "[OCR→RAG] Starting auto-index for report_id=%s user_id=%s "
        "ocr_text_len=%d source_filename=%s",
        report_id, str(user_uuid), len(text), source_file_name,
    )
    try:
        n = index_report(
            report_id=report_id,
            user_id=str(user_uuid),
            ocr_text=text,
            source_filename=source_file_name,
            source_url=public_url,
            report_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        )
        _log.info(
            "[OCR→RAG] Auto-indexed %d chunks for report_id=%s — "
            "pipeline: OCR text → clean → chunk → embed → vector DB",
            n, report_id,
        )
    except Exception as exc:  # noqa: BLE001
        _log.error(
            "[OCR→RAG] Chunk indexing FAILED for report_id=%s (non-fatal). "
            "Exception type: %s — Message: %s. "
            "The report_chunks table may be empty for this report. "
            "Check: 1) DB migrations applied? 2) pgvector extension enabled? "
            "3) sentence-transformers installed? 4) BAAI/bge-base-en-v1.5 downloadable?",
            report_id, type(exc).__name__, exc,
            exc_info=True,
        )

    return text, confidence, report_id


def extract_labs_for_report(
    client: Client,
    report_id: str,
) -> int:
    """Fetch OCR text for a report and extract lab results into lab_results."""
    if not report_id:
        raise ReportOCRError("report_id is required.")

    try:
        uuid.UUID(report_id)
    except ValueError as exc:
        raise ReportOCRError("report_id must be a valid UUID.") from exc

    try:
        response = (
            client.table("medical_reports")
            .select("ocr_text")
            .eq("id", report_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise ReportOCRError(f"Failed to fetch OCR text: {exc}") from exc

    data = response.data or []
    if not data:
        raise ReportOCRError("Report not found.")

    ocr_text = data[0].get("ocr_text") or ""
    return process_report_ocr(client=client, report_id=report_id, ocr_text=ocr_text)


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
    """Run OCR then Gemini extraction on a pre-created pending report row.

    Designed to be called as a FastAPI ``BackgroundTask`` so it executes
    **after** the HTTP 202 response has been sent.  Each request gets its own
    invocation, enabling multiple clients to be processed in parallel (each
    background task runs in a separate thread managed by the ASGI server).

    Pipeline:
        1. Download report bytes from Supabase Storage.
        2. Run Tesseract OCR (PDF → per-page; image → single pass).
        3. Update the ``medical_reports`` row with OCR text + status.
        4. Auto-index chunks for RAG retrieval (best-effort).
        5. Run Gemini extraction → inserts rows into ``lab_results``.
        6. Mark status as ``done`` (or ``failed`` on any error).
    """
    _log.info("Background pipeline started for report_id=%s", report_id)

    # ------------------------------------------------------------------ #
    # Stage 1 — OCR                                                        #
    # ------------------------------------------------------------------ #
    try:
        report_bytes = client.storage.from_(bucket).download(storage_path)
    except Exception as exc:
        msg = f"Storage download failed: {exc}"
        _log.error("report_id=%s — %s", report_id, msg)
        _update_report_status(client, table, report_id, "failed", error=msg)
        return

    try:
        if storage_path.lower().endswith(".pdf"):
            ocr_text, confidence = _extract_text_from_pdf(report_bytes)
        else:
            ocr_text, confidence = _extract_text_from_image(report_bytes)
    except Exception as exc:
        msg = f"OCR failed: {exc}"
        _log.error("report_id=%s — %s", report_id, msg)
        _update_report_status(client, table, report_id, "failed", error=msg)
        return

    _update_report_status(
        client,
        table,
        report_id,
        "ocr_complete",
        extra={"ocr_text": ocr_text, "ocr_engine": "tesseract", "ocr_confidence": confidence},
    )
    _log.info("OCR complete for report_id=%s (confidence=%.1f%%)", report_id, confidence)

    # ------------------------------------------------------------------ #
    # Stage 2 — RAG indexing (best-effort, non-fatal)                     #
    # ------------------------------------------------------------------ #
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
        _log.warning("Chunk indexing failed for report_id=%s (non-fatal): %s", report_id, exc)

    # ------------------------------------------------------------------ #
    # Stage 3 — Gemini extraction                                         #
    # ------------------------------------------------------------------ #
    try:
        process_report_with_gemini(client=client, report_id=report_id)
    except Exception as exc:
        msg = f"Gemini extraction failed: {exc}"
        _log.error("report_id=%s — %s", report_id, msg)
        # OCR succeeded — mark as ocr_complete rather than fully failed so the
        # caller can still retrieve OCR text and retry Gemini separately.
        _update_report_status(client, table, report_id, "failed", error=msg)
        return

    _update_report_status(client, table, report_id, "done")
    _log.info("Pipeline complete for report_id=%s", report_id)
