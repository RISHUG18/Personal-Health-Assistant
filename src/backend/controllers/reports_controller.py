"""Business logic for uploading medical reports to Supabase storage."""
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Tuple

from supabase import Client
import pytesseract

import cv2
import numpy as np
from pdf2image import convert_from_bytes

from backend.ocr2.preprocessor import preprocess_image
from backend.ocr2.ocr_engine import run_ocr
from backend.ocr.pipeline import process_report_ocr
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
def build_report_path(user_id: str, original_filename: str) -> str:
    """Create a unique, user-scoped path for the uploaded report."""
    # Combine user scope, timestamp, and UUID to avoid collisions.
    safe_filename = _sanitize_filename(original_filename)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    unique_id = uuid.uuid4().hex
    return f"{user_id}/{timestamp}_{unique_id}_{safe_filename}"


def upload_medical_report(
    client: Client,
    bucket: str,
    user_id: str,
    original_filename: str,
    file_bytes: bytes,
    content_type: str,
) -> Tuple[str, str]:
    """Upload raw file bytes to Supabase storage and return storage path and public URL.

    Validates inputs, creates a unique storage path for the user, uploads the
    bytes to the specified `bucket`, and returns the storage path along with
    a public URL. Raises `ReportUploadError` on failure.
    """
    if not user_id:
        raise ReportUploadError("user_id is required for report uploads.")
    if not file_bytes:
        raise ReportUploadError("Uploaded file is empty.")

    # Build a unique storage path to keep reports separated by user and upload time.
    storage_path = build_report_path(user_id, original_filename)
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
    try:
        n = index_report(
            report_id=report_id,
            user_id=str(user_uuid),
            ocr_text=text,
        )
        _log.info("Auto-indexed %d chunks for report_id=%s", n, report_id)
    except Exception as exc:  # noqa: BLE001
        _log.warning(
            "Chunk indexing failed for report_id=%s (non-fatal): %s", report_id, exc
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
