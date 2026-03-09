"""Rules engine — fetches lab data from Supabase and evaluates all 13 rules."""

from __future__ import annotations

import logging
from typing import List

from backend.rules.definitions import ALL_RULES, LabRow
from backend.rules.models import AlertRecord

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DB helpers (used internally + exported for testing/debugging)
# ---------------------------------------------------------------------------

def _fetch_reports(client, user_id: str) -> dict:
    """Return ``{report_id: report_row}`` for *user_id*."""
    resp = (
        client.table("medical_reports")
        .select("id, report_date, source_file_name")
        .eq("user_id", user_id)
        .execute()
    )
    return {r["id"]: r for r in (resp.data or [])}


def _fetch_lab_results(client, report_ids: List[str]) -> List[dict]:
    """Return all ``lab_results`` rows for the given report IDs."""
    if not report_ids:
        return []
    resp = (
        client.table("lab_results")
        .select("id, report_id, test_name, value, unit, reference_range, abnormal_flag")
        .in_("report_id", report_ids)
        .execute()
    )
    return resp.data or []


def _build_lab_rows(report_map: dict, raw_labs: List[dict]) -> List[LabRow]:
    """Convert raw Supabase dicts into :class:`LabRow` value objects."""
    rows: List[LabRow] = []
    for lab in raw_labs:
        report  = report_map.get(lab.get("report_id"), {})
        raw_val = lab.get("value")
        try:
            value: float | None = float(raw_val) if raw_val is not None else None
        except (TypeError, ValueError):
            value = None

        test_name = lab.get("test_name") or ""
        rows.append(
            LabRow(
                lab_result_id=lab.get("id") or "",
                report_id=lab.get("report_id") or "",
                test_name=test_name,
                value=value,
                unit=lab.get("unit"),
                reference_range=lab.get("reference_range"),
                abnormal_flag=lab.get("abnormal_flag"),
                report_date=report.get("report_date"),
                ocr_snippet=(
                    f"{test_name}  {raw_val}  {lab.get('unit') or ''}".strip()
                ),
            )
        )
    return rows


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate_rules(client, user_id: str) -> List[AlertRecord]:
    """Evaluate all 13 rules against the user's lab data.

    Fetches ``medical_reports`` + ``lab_results`` from Supabase, converts
    them to :class:`LabRow` objects, runs each rule, and returns only the
    :class:`AlertRecord` instances where ``triggered=True``.
    """
    report_map = _fetch_reports(client, user_id)
    if not report_map:
        _log.info("No reports found for user_id=%s — no rules evaluated.", user_id)
        return []

    raw_labs = _fetch_lab_results(client, list(report_map.keys()))
    lab_rows = _build_lab_rows(report_map, raw_labs)

    _log.info(
        "Evaluating %d rules against %d lab rows for user_id=%s",
        len(ALL_RULES), len(lab_rows), user_id,
    )

    triggered: List[AlertRecord] = []
    for rule_def in ALL_RULES:
        try:
            result = rule_def.func(user_id, lab_rows)
        except Exception as exc:  # noqa: BLE001
            _log.warning("Rule %s raised an exception: %s", rule_def.rule_id, exc)
            continue
        if result.triggered:
            triggered.append(result)

    _log.info("%d/%d rules triggered for user_id=%s", len(triggered), len(ALL_RULES), user_id)
    return triggered
