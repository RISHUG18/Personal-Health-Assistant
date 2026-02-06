"""Pipeline to extract deterministic lab results and insert into Postgres."""
from __future__ import annotations

import uuid
from typing import Iterable, List

from supabase import Client

from .extractors import LabExtraction, extract_lab_results
from .inserters import insert_lab_results


def process_report_ocr(
    client: Client,
    report_id: str,
    ocr_text: str,
) -> int:
    """Extract lab results from OCR text and insert rows into lab_results.

    Returns the number of inserted rows. OCR text is never modified.
    """
    if not ocr_text:
        return 0

    try:
        uuid.UUID(report_id)
    except ValueError:
        return 0

    lab_results = extract_lab_results(ocr_text)
    if not lab_results:
        return 0

    return insert_lab_results(client=client, report_id=report_id, lab_results=lab_results)
