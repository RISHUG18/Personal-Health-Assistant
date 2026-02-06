"""Database insertion helpers for deterministic OCR extraction."""
from __future__ import annotations

import uuid
from typing import Iterable, List

from supabase import Client

from .normalizers import parse_numeric_range
from .extractors import LabExtraction


def _compute_abnormal_flag(value: float, reference_range: str | None) -> bool | None:
    if not reference_range:
        return None
    low, high = parse_numeric_range(reference_range)
    if low is None or high is None:
        return None
    if value < low:
        return True
    if value > high:
        return True
    return False


def insert_lab_results(
    client: Client,
    report_id: str,
    lab_results: Iterable[LabExtraction],
) -> int:
    """Insert validated lab results into lab_results. Returns rows inserted."""
    payload: List[dict] = []
    for item in lab_results:
        payload.append(
            {
                "id": str(uuid.uuid4()),
                "report_id": report_id,
                "test_name": item.test_name,
                "value": item.value,
                "unit": item.unit,
                "reference_range": item.reference_range,
                "abnormal_flag": _compute_abnormal_flag(item.value, item.reference_range),
                "extracted_from_page": item.extracted_from_page,
            }
        )

    if not payload:
        return 0

    client.table("lab_results").insert(payload).execute()
    return len(payload)
