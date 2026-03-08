"""Full Gemini extraction pipeline: fetch OCR → extract → normalise → insert → log.

This module orchestrates the end-to-end extraction of structured lab data from
a medical report's OCR text using Google Gemini, then inserts the results into
Supabase.

Usage::

    from backend.extraction.pipeline import process_report_with_gemini
    from backend.config.supabase_client import get_supabase_client

    client = get_supabase_client()
    result = process_report_with_gemini(client=client, report_id="<uuid>")
    print(result)
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from supabase import Client

from backend.config.supabase_client import get_supabase_client
from .gemini_extractor import extract_with_gemini
from .inserter import insert_lab_results, update_report_metadata
from .models import ExtractionLogEntry

logger = logging.getLogger(__name__)


def _setup_extraction_logger() -> logging.Logger:
    """Return a logger that writes detailed extraction logs to both
    console and a file (``extraction.log``) in the working directory.
    """
    ext_logger = logging.getLogger("extraction_pipeline")
    if not ext_logger.handlers:
        ext_logger.setLevel(logging.DEBUG)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        ext_logger.addHandler(ch)

        # File handler
        try:
            fh = logging.FileHandler("extraction.log", mode="a", encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            ))
            ext_logger.addHandler(fh)
        except OSError:
            ext_logger.warning("Could not create extraction.log file handler.")

    return ext_logger


def process_report_with_gemini(
    client: Optional[Client] = None,
    report_id: str = "",
) -> dict:
    """Run the full Gemini extraction pipeline for a medical report.

    Pipeline steps:
    1. Fetch OCR text from ``medical_reports``
    2. Send OCR text to Gemini for structured extraction
    3. Normalise extracted data (units, dates)
    4. Insert into ``lab_results`` (idempotent — deletes old rows first)
    5. Update ``medical_reports`` metadata (report_date, report_type)
    6. Return complete result with extraction log

    Parameters
    ----------
    client:
        Optional Supabase client; defaults to the global singleton.
    report_id:
        UUID of the ``medical_reports`` row to process.

    Returns
    -------
    dict
        Complete result including extraction log, inserted count, and any errors.

    Raises
    ------
    ValueError
        If ``report_id`` is empty or not a valid UUID.
    RuntimeError
        If OCR text cannot be fetched or Gemini extraction fails.
    """
    log = _setup_extraction_logger()
    db = client or get_supabase_client()

    # ── Validation ────────────────────────────────────────────────────────────
    if not report_id:
        raise ValueError("report_id must not be empty.")

    import uuid as _uuid
    try:
        _uuid.UUID(report_id)
    except ValueError as exc:
        raise ValueError(f"report_id is not a valid UUID: {exc}") from exc

    extraction_log = ExtractionLogEntry(report_id=report_id)
    start_time = time.time()

    log.info("=" * 70)
    log.info("EXTRACTION PIPELINE START — report_id=%s", report_id)
    log.info("=" * 70)

    # ── Step 1: Fetch OCR text ────────────────────────────────────────────────
    log.info("[Step 1/5] Fetching OCR text from medical_reports…")
    try:
        response = (
            db.table("medical_reports")
            .select("ocr_text, source_file_name")
            .eq("id", report_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        msg = f"Database query failed: {exc}"
        extraction_log.errors.append(msg)
        log.error(msg)
        raise RuntimeError(msg) from exc

    data = response.data or []
    if not data:
        msg = f"No medical_reports row found for report_id={report_id}"
        extraction_log.errors.append(msg)
        log.error(msg)
        raise RuntimeError(msg)

    ocr_text = data[0].get("ocr_text") or ""
    source_file = data[0].get("source_file_name") or "unknown"

    if not ocr_text.strip():
        msg = "OCR text is empty — nothing to extract."
        extraction_log.warnings.append(msg)
        log.warning(msg)
        return {
            "report_id": report_id,
            "inserted": 0,
            "skipped": 0,
            "extraction_log": extraction_log.model_dump(),
        }

    log.info(
        "  OCR text retrieved: %d characters from '%s'",
        len(ocr_text), source_file,
    )

    # ── Step 2: Gemini extraction ─────────────────────────────────────────────
    log.info("[Step 2/5] Sending OCR text to Gemini for structured extraction…")
    try:
        gemini_result = extract_with_gemini(ocr_text)
    except Exception as exc:
        msg = f"Gemini extraction failed: {exc}"
        extraction_log.errors.append(msg)
        log.error(msg)
        raise RuntimeError(msg) from exc

    extraction_log.total_tests_found = len(gemini_result.lab_results)
    log.info(
        "  Gemini extracted %d lab results", len(gemini_result.lab_results)
    )

    if gemini_result.extraction_notes:
        extraction_log.warnings.append(
            f"Gemini notes: {gemini_result.extraction_notes}"
        )
        log.info("  Gemini notes: %s", gemini_result.extraction_notes)

    # Log each extracted result
    log.info("[Step 3/5] Extracted lab results detail:")
    for i, lab in enumerate(gemini_result.lab_results, 1):
        log.info(
            "  [%d] %-35s = %s %s  (ref: %s, abnormal: %s, page: %s)",
            i,
            lab.test_name,
            lab.value if lab.value is not None else lab.value_string,
            lab.unit or "",
            lab.reference_range or "—",
            lab.is_abnormal,
            lab.page_number,
        )

    # Log metadata
    meta = gemini_result.metadata
    log.info("  Report metadata:")
    log.info("    Date:    %s", meta.report_date or "—")
    log.info("    Type:    %s", meta.report_type or "—")
    log.info("    Patient: %s", meta.patient_name or "—")
    log.info("    Lab:     %s", meta.lab_name or "—")

    # ── Step 4: Insert into lab_results ───────────────────────────────────────
    log.info("[Step 4/5] Inserting lab results into database (idempotent)…")
    try:
        inserted, skipped, skip_reasons = insert_lab_results(
            client=db,
            report_id=report_id,
            lab_results=gemini_result.lab_results,
        )
    except Exception as exc:
        msg = f"Database insertion failed: {exc}"
        extraction_log.errors.append(msg)
        log.error(msg)
        raise RuntimeError(msg) from exc

    extraction_log.tests_inserted = inserted
    extraction_log.tests_skipped = skipped
    extraction_log.skipped_details = skip_reasons

    log.info("  Inserted: %d rows", inserted)
    if skipped > 0:
        log.info("  Skipped:  %d rows", skipped)
        for reason in skip_reasons:
            log.info("    → %s", reason)

    # ── Step 5: Update report metadata ────────────────────────────────────────
    log.info("[Step 5/5] Updating medical_reports metadata…")
    metadata_updates = update_report_metadata(
        client=db,
        report_id=report_id,
        metadata=gemini_result.metadata,
    )
    extraction_log.metadata_updates = metadata_updates
    if metadata_updates:
        for key, val in metadata_updates.items():
            log.info("  Updated %s = %s", key, val)
    else:
        log.info("  No metadata updates applied.")

    # ── Summary ───────────────────────────────────────────────────────────────
    elapsed = time.time() - start_time
    log.info("-" * 70)
    log.info("EXTRACTION PIPELINE COMPLETE — report_id=%s", report_id)
    log.info("  Total tests found:  %d", extraction_log.total_tests_found)
    log.info("  Tests inserted:     %d", extraction_log.tests_inserted)
    log.info("  Tests skipped:      %d", extraction_log.tests_skipped)
    log.info("  Errors:             %d", len(extraction_log.errors))
    log.info("  Warnings:           %d", len(extraction_log.warnings))
    log.info("  Time elapsed:       %.2f seconds", elapsed)
    log.info("=" * 70)

    return {
        "report_id": report_id,
        "source_file": source_file,
        "inserted": inserted,
        "skipped": skipped,
        "metadata_updates": metadata_updates,
        "extraction_log": extraction_log.model_dump(),
        "gemini_notes": gemini_result.extraction_notes,
        "elapsed_seconds": round(elapsed, 2),
    }
