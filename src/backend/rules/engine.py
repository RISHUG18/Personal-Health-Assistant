"""Rules evaluation engine.

Responsibilities
----------------
1. Fetch all lab_results for a user (two-step: reports → lab rows).
2. Run every RuleDefinition against the fetched rows.
3. Return triggered AlertRecord objects — ready for the persistence layer.

Design decisions
----------------
- Two separate queries instead of a PostgREST join: more reliable with the
  Supabase Python client v2 and easier to reason about.
- Rules are evaluated in isolation; one rule failing does NOT abort others.
- No writes happen here — engine is read-only.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from supabase import Client

from .definitions import ALL_RULES, LabRow, RuleDefinition
from .models import AlertRecord, Severity

logger = logging.getLogger(__name__)


# ── Data fetching ─────────────────────────────────────────────────────────────


def _fetch_reports(client: Client, user_id: str) -> dict[str, dict]:
    """Return a mapping {report_id: report_row} for all reports owned by user.

    Fetches only the columns needed by the engine: id, report_date, ocr_text.
    """
    try:
        resp = (
            client.table("medical_reports")
            .select("id, report_date, ocr_text")
            .eq("user_id", user_id)
            .execute()
        )
    except Exception as exc:
        logger.error("Failed to fetch medical_reports for user_id=%s: %s", user_id, exc)
        return {}

    return {row["id"]: row for row in (resp.data or [])}


def _fetch_lab_results(client: Client, report_ids: List[str]) -> List[dict]:
    """Return all lab_results rows for the given report IDs."""
    if not report_ids:
        return []
    try:
        resp = (
            client.table("lab_results")
            .select("id, report_id, test_name, value, unit, reference_range, abnormal_flag")
            .in_("report_id", report_ids)
            .execute()
        )
        return resp.data or []
    except Exception as exc:
        logger.error("Failed to fetch lab_results for %d reports: %s", len(report_ids), exc)
        return []


def _find_ocr_snippet(ocr_text: str, test_name: str) -> Optional[str]:
    """Return the first OCR line that contains the test name (≤ 200 chars).

    Used to populate EvidenceRef.ocr_text_snippet so that each alert has a
    verbatim reference back to the source document.
    """
    if not ocr_text or not test_name:
        return None
    target = test_name.lower()
    for line in ocr_text.splitlines():
        if target in line.lower():
            return line.strip()[:200]
    return None


def _build_lab_rows(
    report_map: dict[str, dict],
    raw_lab_rows: List[dict],
) -> List[LabRow]:
    """Combine lab_results rows with their parent report data into LabRow objects."""
    rows: List[LabRow] = []
    skipped = 0

    for item in raw_lab_rows:
        report = report_map.get(item.get("report_id", ""))
        if report is None:
            skipped += 1
            continue

        ocr_text: str = report.get("ocr_text") or ""
        test_name: str = item.get("test_name") or ""

        rows.append(
            LabRow(
                lab_result_id=item["id"],
                report_id=item["report_id"],
                test_name=test_name,
                value=item.get("value"),
                unit=item.get("unit"),
                reference_range=item.get("reference_range"),
                abnormal_flag=item.get("abnormal_flag"),
                report_date=report.get("report_date"),
                ocr_snippet=_find_ocr_snippet(ocr_text, test_name),
            )
        )

    if skipped:
        logger.warning(
            "Skipped %d lab rows with unresolvable report_id", skipped
        )
    return rows


# ── Engine ────────────────────────────────────────────────────────────────────


def evaluate_rules(
    client: Client,
    user_id: str,
    rules: Optional[List[RuleDefinition]] = None,
) -> List[AlertRecord]:
    """Run all rules against the user's lab data and return triggered alerts.

    Parameters
    ----------
    client:
        Supabase client instance.
    user_id:
        UUID of the user whose data is being evaluated.
    rules:
        Override the default rule registry.  Mainly useful for tests.

    Returns
    -------
    List[AlertRecord]
        One AlertRecord per triggered rule.  Empty list if no rules fired
        or if the user has no lab data.

    Notes
    -----
    - One failing rule never aborts the others; exceptions are caught and
      logged individually.
    - The function is idempotent and read-only — it never writes to the DB.
    """
    rule_set = rules if rules is not None else ALL_RULES

    # ── Step 1: Fetch data ───────────────────────────────────────────────────
    report_map = _fetch_reports(client, user_id)
    if not report_map:
        logger.warning(
            "No medical_reports found for user_id=%s — skipping rule evaluation.", user_id
        )
        return []

    raw_labs = _fetch_lab_results(client, list(report_map.keys()))
    lab_rows = _build_lab_rows(report_map, raw_labs)

    logger.info(
        "Loaded %d reports, %d lab rows for user_id=%s",
        len(report_map), len(lab_rows), user_id,
    )

    if not lab_rows:
        logger.warning(
            "No lab_results found for user_id=%s — skipping rule evaluation.", user_id
        )
        return []

    # ── Step 2: Evaluate each rule ───────────────────────────────────────────
    alerts: List[AlertRecord] = []
    triggered_count = 0
    skipped_count = 0

    for rule_def in rule_set:
        try:
            result = rule_def.func(user_id, lab_rows)
        except Exception as exc:
            skipped_count += 1
            logger.error(
                "Rule '%s' raised an unhandled exception for user_id=%s: %s",
                rule_def.rule_id, user_id, exc,
                exc_info=True,
            )
            continue

        if not result.triggered:
            logger.debug(
                "Rule '%s' → NOT triggered for user_id=%s",
                rule_def.rule_id, user_id,
            )
            continue

        triggered_count += 1
        logger.info(
            "Rule '%s' → TRIGGERED | user_id=%s | severity=%s | reason=%s",
            rule_def.rule_id, user_id, result.severity, result.reason,
        )

        alerts.append(
            AlertRecord(
                user_id=user_id,
                severity=result.severity,
                reason=result.reason,
                timestamp=datetime.now(timezone.utc),
                evidence_refs=result.evidence_refs,
            )
        )

    # ── Step 3: Summary log ──────────────────────────────────────────────────
    logger.info(
        "Rule evaluation complete for user_id=%s: %d/%d rules triggered, %d skipped due to errors",
        user_id, triggered_count, len(rule_set), skipped_count,
    )

    return alerts
