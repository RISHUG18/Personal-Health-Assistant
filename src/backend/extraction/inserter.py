"""Idempotent database insertion for Gemini-extracted lab data.

Inserts normalised lab results into ``lab_results`` and optionally updates
``medical_reports`` metadata (report_date, report_type).

Idempotency:
    Calling this function multiple times for the same ``report_id`` is safe.
    Existing lab_results rows for the report are deleted before re-insertion,
    ensuring the latest extraction always wins.
"""

from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from supabase import Client

from .models import ExtractedLabResult, ExtractedReportMetadata
from .normalizer import (
    normalize_date,
    normalize_reference_range,
    normalize_test_name,
    normalize_unit,
    parse_numeric_range,
)

logger = logging.getLogger(__name__)


def _compute_abnormal_flag(
    value: Optional[float],
    reference_range: Optional[str],
    gemini_flag: Optional[bool],
) -> Optional[bool]:
    """Determine abnormal flag with priority: Gemini flag → range check → None.

    1. If Gemini already flagged it, trust that (it reads H/L/* markers).
    2. Else, if we can parse a numeric range, compare the value.
    3. Otherwise return None (don't guess).
    """
    if gemini_flag is not None:
        return gemini_flag

    if value is None or reference_range is None:
        return None

    low, high = parse_numeric_range(reference_range)
    if low is None or high is None:
        return None

    return value < low or value > high


def insert_lab_results(
    client: Client,
    report_id: str,
    lab_results: List[ExtractedLabResult],
) -> tuple[int, int, list[str]]:
    """Insert Gemini-extracted lab results into the ``lab_results`` table.

    Deletes any existing rows for this report first (idempotency).

    Parameters
    ----------
    client:
        Supabase client instance.
    report_id:
        UUID of the parent ``medical_reports`` row.
    lab_results:
        List of extracted lab results from Gemini.

    Returns
    -------
    tuple[int, int, list[str]]
        ``(inserted_count, skipped_count, skip_reasons)``
    """
    # ── 1. Delete existing lab results for this report (idempotency) ──────────
    try:
        client.table("lab_results").delete().eq("report_id", report_id).execute()
        logger.info("Cleared existing lab_results for report_id=%s", report_id)
    except Exception as exc:
        logger.warning(
            "Failed to clear old lab_results for report_id=%s: %s", report_id, exc
        )

    # ── 2. Build payload ─────────────────────────────────────────────────────
    payload: list[dict] = []
    skipped: list[str] = []

    for item in lab_results:
        test_name = normalize_test_name(item.test_name)

        # Skip if no test name
        if not test_name:
            skipped.append("Skipped: empty test_name")
            continue

        # Skip if there's no numeric value AND no string value
        if item.value is None and not item.value_string:
            skipped.append(f"Skipped '{test_name}': no value (numeric or string)")
            continue

        unit = normalize_unit(item.unit)
        ref_range = normalize_reference_range(item.reference_range)
        abnormal = _compute_abnormal_flag(item.value, ref_range, item.is_abnormal)

        payload.append(
            {
                "id": str(uuid.uuid4()),
                "report_id": report_id,
                "test_name": test_name,
                "value": item.value,  # NUMERIC — None for non-numeric results
                "text_value": item.value_string, # TEXT — for non-numeric string data
                "unit": unit,
                "reference_range": ref_range,
                "abnormal_flag": abnormal,
                "extracted_from_page": item.page_number,
            }
        )

    if not payload:
        logger.warning("No lab results to insert for report_id=%s", report_id)
        return 0, len(skipped), skipped

    # ── 3. Batch insert ──────────────────────────────────────────────────────
    try:
        client.table("lab_results").insert(payload).execute()
        logger.info(
            "Inserted %d lab_results for report_id=%s", len(payload), report_id
        )
    except Exception as exc:
        logger.error("Failed to insert lab_results: %s", exc)
        raise RuntimeError(f"Database insertion failed: {exc}") from exc

    return len(payload), len(skipped), skipped


def update_report_metadata(
    client: Client,
    report_id: str,
    metadata: ExtractedReportMetadata,
) -> dict:
    """Update ``medical_reports`` with extracted metadata (date, type).

    Only updates fields that are not None in the metadata.

    Returns
    -------
    dict
        Mapping of field names to the values that were updated.
    """
    updates: dict = {}

    # Normalize and set report_date
    if metadata.report_date:
        iso_date = normalize_date(metadata.report_date)
        if iso_date:
            updates["report_date"] = iso_date

    # Set report_type
    if metadata.report_type:
        updates["report_type"] = metadata.report_type.strip()

    if not updates:
        logger.info(
            "No metadata to update for report_id=%s", report_id
        )
        return {}

    try:
        client.table("medical_reports").update(updates).eq("id", report_id).execute()
        logger.info(
            "Updated medical_reports metadata for report_id=%s: %s",
            report_id, updates,
        )
    except Exception as exc:
        # Metadata update failure is non-fatal
        logger.warning(
            "Failed to update report metadata for report_id=%s: %s", report_id, exc
        )
        return {}

    return updates
