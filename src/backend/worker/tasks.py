"""Celery tasks for asynchronous medical report processing.

Pipeline (runs inside a Celery worker process)
-----------------------------------------------
1.  Download report bytes from Supabase Storage.
2.  Convert PDF/image → list of PIL Images.
3.  Tesseract OCR — extract text from every page.
4.  Update DB: ``ocr_complete`` + OCR text/confidence.
5.  Gemini AI — parse OCR text into structured lab results.
6.  Validate (non-empty text, confidence ≥ 25 %, ≥ 1 test).
7.  Insert lab results + update report metadata.
8.  RAG indexing — best-effort, non-fatal.
9.  Mark DB: ``done``; publish ``completed`` to Redis pub/sub.
10. Evaluate alert rules + persist alerts — best-effort.

Status updates are published to the Redis channel
``report:status:<report_id>`` and are consumed by the FastAPI
process which forwards them to subscribed WebSocket clients.
"""
from __future__ import annotations

import io
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import redis
from celery import Task
from dotenv import load_dotenv
from PIL import Image
from pdf2image import convert_from_bytes

# Ensure env vars are loaded in the worker process.
_ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(_ENV_FILE, override=False)

from backend.worker.celery_app import celery_app
from backend.config.supabase_client import (
    get_ocr_reports_table,
    get_reports_bucket,
    get_supabase_client,
)
from backend.extraction.gemini_extractor import extract_with_gemini
from backend.extraction.inserter import insert_lab_results, update_report_metadata
from backend.ocr.ocr_engine import run_ocr
from backend.ocr.preprocessor import preprocess_image
from backend.services.retrieval.indexer import index_report

_log = logging.getLogger(__name__)

# Redis pub/sub channel pattern: one channel per report.
_REDIS_CHANNEL_PREFIX = "report:status:"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clamp_confidence(confidence: float) -> float:
    """Normalize a 0-100 confidence value to the 0.0-1.0 range."""
    if confidence < 0:
        return 0.0
    if confidence > 100:
        return 1.0
    return round(confidence / 100.0, 4)


def _get_redis_client() -> redis.Redis:
    """Return a synchronous Redis client (used inside Celery tasks)."""
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return redis.from_url(url, decode_responses=True)


def _publish_status(
    r: redis.Redis,
    report_id: str,
    status: str,
    data: Optional[dict] = None,
    error: Optional[dict] = None,
) -> None:
    """Publish a status update message to the Redis pub/sub channel."""
    message = {
        "report_id": report_id,
        "status": status,
        "data": data or {},
        "error": error or {},
    }
    channel = f"{_REDIS_CHANNEL_PREFIX}{report_id}"
    try:
        r.publish(channel, json.dumps(message))
        _log.debug("Published status=%s to %s", status, channel)
    except Exception as exc:  # noqa: BLE001
        _log.warning("Redis publish failed for report_id=%s status=%s: %s", report_id, status, exc)


def _update_db_status(
    client,
    table: str,
    report_id: str,
    status: str,
    error: Optional[str] = None,
    extra: Optional[dict] = None,
) -> None:
    """Best-effort update of processing_status on the report row."""
    payload: dict = {"processing_status": status}
    if error is not None:
        payload["processing_error"] = error
    if extra:
        payload.update(extra)
    try:
        client.table(table).update(payload).eq("id", report_id).execute()
    except Exception as exc:  # noqa: BLE001
        _log.warning("DB status update failed for report_id=%s: %s", report_id, exc)


def _cleanup_artifacts(
    client,
    bucket: str,
    table: str,
    report_id: str,
    storage_path: str,
    *,
    delete_report_row: bool = False,
) -> None:
    """Remove storage file, lab results, and report chunks after a failure."""
    if storage_path:
        try:
            client.storage.from_(bucket).remove([storage_path])
        except Exception as exc:  # noqa: BLE001
            _log.warning("Could not delete storage file '%s': %s", storage_path, exc)

    for table_name, filter_col in [
        ("lab_results", "report_id"),
        ("report_chunks", "report_id"),
    ]:
        try:
            client.table(table_name).delete().eq(filter_col, report_id).execute()
        except Exception as exc:  # noqa: BLE001
            _log.warning("Could not clean %s for report_id=%s: %s", table_name, report_id, exc)

    if delete_report_row:
        try:
            client.table(table).delete().eq("id", report_id).execute()
        except Exception as exc:  # noqa: BLE001
            _log.warning("Could not delete report row for report_id=%s: %s", report_id, exc)


def _pdf_bytes_to_images(pdf_bytes: bytes) -> list[Image.Image]:
    return convert_from_bytes(pdf_bytes)


def _image_bytes_to_pil(image_bytes: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(image_bytes))
    img.load()
    return img


def _run_tesseract(images: list[Image.Image]) -> tuple[str, float]:
    """Run Tesseract OCR over all pages; return (full_text, avg_confidence)."""
    page_texts: list[str] = []
    confidences: list[float] = []

    for page_num, pil_img in enumerate(images, start=1):
        img_array = np.array(pil_img.convert("RGB"))[..., ::-1]  # RGB → BGR
        preprocessed = preprocess_image(img_array)
        text, conf = run_ocr(preprocessed)
        page_texts.append(f"--- Page {page_num} ---\n{text}")
        if conf >= 0:
            confidences.append(conf)
        _log.info(
            "OCR page %d/%d: %d chars, confidence=%.1f%%",
            page_num, len(images), len(text), conf,
        )

    full_text = "\n\n".join(page_texts)
    avg_confidence = float(sum(confidences) / len(confidences)) if confidences else 0.0
    return full_text, avg_confidence


def _validate_extraction(
    ocr_text: str,
    ocr_confidence: float,
    tests_detected: int,
) -> tuple[bool, str]:
    """Return ``(is_valid, reason)`` for the extracted report content."""
    if not ocr_text.strip():
        return False, "OCR produced empty text"
    if ocr_confidence < 25.0:
        return False, "OCR confidence too low"
    if tests_detected <= 0:
        return False, "No valid lab tests detected"
    return True, ""


# ── Celery Task ───────────────────────────────────────────────────────────────

@celery_app.task(
    bind=True,
    name="backend.worker.tasks.process_report",
    max_retries=3,
    default_retry_delay=10,
    acks_late=True,
)
def process_report(
    self: Task,
    report_id: str,
    storage_path: str,
    user_id: str,
) -> dict:
    """Run the full report processing pipeline asynchronously.

    This task is enqueued by the FastAPI ``POST /reports/ingest`` endpoint
    immediately after creating the ``pending`` DB row.  Status updates are
    published to Redis so the API WebSocket subscriber can forward them to
    connected frontend clients in real time.

    Parameters
    ----------
    report_id:
        UUID of the ``medical_reports`` row created by the API.
    storage_path:
        Supabase Storage path of the uploaded file.
    user_id:
        UUID of the report owner (used for alerts and indexing).
    """
    _log.info(
        "[task=%s] Pipeline started for report_id=%s user_id=%s",
        self.request.id, report_id, user_id,
    )

    # Set up shared clients
    r = _get_redis_client()
    client = get_supabase_client()
    bucket = get_reports_bucket()
    table = get_ocr_reports_table()

    # Convenience closures to keep pipeline stages readable
    def db(status: str, error: Optional[str] = None, extra: Optional[dict] = None) -> None:
        _update_db_status(client, table, report_id, status, error=error, extra=extra)

    def pub(
        status: str,
        data: Optional[dict] = None,
        error: Optional[dict] = None,
    ) -> None:
        _publish_status(r, report_id, status, data=data, error=error)

    def fail(reason: str, confidence: float = 0.0, *, delete_row: bool = False) -> None:
        db("failed", error=reason)
        _cleanup_artifacts(
            client, bucket, table, report_id, storage_path,
            delete_report_row=delete_row,
        )
        pub(
            "failed",
            data={"cleanup_completed": True, "report_deleted": delete_row},
            error={"reason": reason, "confidence": _clamp_confidence(confidence)},
        )

    # Signal processing has started
    pub("processing")

    # ── Stage 1: Download ─────────────────────────────────────────────────────
    try:
        report_bytes = client.storage.from_(bucket).download(storage_path)
    except Exception as exc:
        fail(f"Storage download failed: {exc}")
        return {"status": "failed", "stage": "download"}

    # ── Stage 2: Convert to images ────────────────────────────────────────────
    try:
        if storage_path.lower().endswith(".pdf"):
            images = _pdf_bytes_to_images(report_bytes)
        else:
            images = [_image_bytes_to_pil(report_bytes)]
    except Exception as exc:
        fail(f"Image conversion failed: {exc}")
        return {"status": "failed", "stage": "image_conversion"}

    # ── Stage 3: Tesseract OCR ────────────────────────────────────────────────
    try:
        ocr_text, ocr_confidence = _run_tesseract(images)
    except Exception as exc:
        fail(f"Tesseract OCR failed: {exc}")
        return {"status": "failed", "stage": "ocr"}

    _log.info(
        "OCR complete for report_id=%s (chars=%d, confidence=%.1f%%)",
        report_id, len(ocr_text), ocr_confidence,
    )
    
    pub("ocr_complete")

    # ── Stage 4: Persist OCR text ─────────────────────────────────────────────
    db(
        "ocr_complete",
        extra={
            "ocr_text": ocr_text,
            "ocr_engine": "tesseract",
            "ocr_confidence": ocr_confidence,
        },
    )

    # ── Stage 5: Gemini lab extraction ────────────────────────────────────────
    try:
        gemini_result = extract_with_gemini(ocr_text)
    except Exception as exc:
        fail(
            f"Gemini lab extraction failed: {exc}",
            confidence=ocr_confidence,
        )
        return {"status": "failed", "stage": "gemini"}

    tests_detected = len(gemini_result.lab_results)
    _log.info(
        "Gemini complete for report_id=%s — %d lab results",
        report_id, tests_detected,
    )
    pub("validating")

    # ── Stage 5b: Validate extraction ─────────────────────────────────────────
    is_valid, invalid_reason = _validate_extraction(ocr_text, ocr_confidence, tests_detected)
    if not is_valid:
        _log.warning("Invalid report report_id=%s: %s", report_id, invalid_reason)
        fail(invalid_reason, confidence=ocr_confidence, delete_row=True)
        return {"status": "failed", "stage": "validation", "reason": invalid_reason}

    # ── Stage 6: Insert lab results ───────────────────────────────────────────
    try:
        inserted, skipped, _ = insert_lab_results(
            client=client,
            report_id=report_id,
            lab_results=gemini_result.lab_results,
        )
        update_report_metadata(
            client=client,
            report_id=report_id,
            metadata=gemini_result.metadata,
        )
        _log.info(
            "Inserted %d lab results (%d skipped) for report_id=%s",
            inserted, skipped, report_id,
        )
    except Exception as exc:
        fail(f"Lab results insertion failed: {exc}", confidence=ocr_confidence)
        return {"status": "failed", "stage": "insert_labs"}

    # ── Stage 7: RAG indexing (best-effort, non-fatal) ────────────────────────
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
        _log.info("Indexed %d chunks for report_id=%s", n, report_id)
    except Exception as exc:  # noqa: BLE001
        _log.warning("RAG indexing failed for report_id=%s (non-fatal): %s", report_id, exc)

    # ── Stage 8: Mark done + notify clients ───────────────────────────────────
    db("done")
    pub(
        "completed",
        data={
            "report_id": report_id,
            "tests_detected": tests_detected,
            "ocr_confidence": _clamp_confidence(ocr_confidence),
        },
    )

    # ── Stage 9: Alert evaluation (best-effort, non-fatal) ───────────────────
    try:
        from backend.rules.engine import evaluate_rules
        from backend.rules.inserter import persist_alerts

        alerts = evaluate_rules(client=client, user_id=user_id)
        persist_result = persist_alerts(client=client, user_id=user_id, alerts=alerts)
        errors = persist_result.get("errors") or []
        if errors:
            _log.warning(
                "Alert persistence warnings for user_id=%s: %s", user_id, errors,
            )
        _log.info(
            "Post-completion: %d alert(s) evaluated for report_id=%s",
            len(alerts), report_id,
        )
    except Exception as exc:  # noqa: BLE001
        _log.warning("Alert evaluation failed for report_id=%s (non-fatal): %s", report_id, exc)

    _log.info(
        "[task=%s] Pipeline complete for report_id=%s (tests=%d)",
        self.request.id, report_id, tests_detected,
    )
    return {
        "status": "done",
        "report_id": report_id,
        "tests_detected": tests_detected,
        "ocr_confidence": _clamp_confidence(ocr_confidence),
        "inserted": inserted,
    }
