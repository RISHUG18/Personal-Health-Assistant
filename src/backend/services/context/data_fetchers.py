"""Database fetch helpers for the context builder.

Each function fetches one slice of data from Supabase and returns a plain dict
(or list of dicts) that :func:`~backend.services.context.context_builder.build_context`
can consume directly.

Design
------
* Fetchers are **thin adapters** between the DB schema and the context builder.
  They do the absolute minimum: query → return dict.  No business logic.
* All functions accept an optional ``client`` parameter so tests can inject a
  fixture/mock without patching globals.
* Errors are caught, logged, and result in an empty fallback so that a missing
  data source never breaks the entire context assembly.

Usage
-----
::

    from backend.services.context.data_fetchers import (
        fetch_active_alerts,
        fetch_user_lab_snapshot,
    )

    alerts  = fetch_active_alerts(user_id="<uuid>")
    snapshot = fetch_user_lab_snapshot(user_id="<uuid>")
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from supabase import Client

from backend.config.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


# ── Alerts ────────────────────────────────────────────────────────────────────

def fetch_active_alerts(
    user_id: str,
    *,
    client: Optional[Client] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Fetch open alerts for *user_id* from the ``alerts`` table.

    Returns a list of dicts compatible with the ``AlertItem`` model::

        [{"id": "...", "severity": "high", "reason": "...", "type": "system"}, ...]

    An empty list is returned if there are no alerts or if the query fails.

    Parameters
    ----------
    user_id:
        UUID of the user whose alerts are fetched.
    client:
        Optional Supabase client; defaults to the global singleton.
    limit:
        Maximum number of alerts to return (most recent first).
    """
    if not user_id:
        return []

    db = client or get_supabase_client()
    try:
        response = (
            db.table("alerts")
            .select("id, severity, reason, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        rows = response.data or []
        # Ensure the 'type' key expected by AlertItem is always present.
        for row in rows:
            row.setdefault("type", "system")
        return rows
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "fetch_active_alerts failed for user_id=%s: %s", user_id, exc
        )
        return []


# ── Structured lab snapshot ───────────────────────────────────────────────────

def fetch_user_lab_snapshot(
    user_id: str,
    *,
    client: Optional[Client] = None,
    max_results: int = 20,
) -> Dict[str, Any]:
    """Fetch the most recent structured lab values for *user_id*.

    Queries ``lab_results`` (joined through ``medical_reports``) and returns
    a dict that maps cleanly onto the ``MedicalSnapshot`` model::

        {
            "last_checkup_date": "2025-10-15",
            "known_conditions": [],
            "recent_vitals": {
                "heart_rate": 72,
                "blood_pressure_systolic": 120,
                "blood_pressure_diastolic": 80,
                "spo2_percentage": 98
            },
            "raw_lab_results": [
                {"test_name": "Hemoglobin A1c", "value": 6.2, "unit": "%",
                 "reference_range": "4.0–5.6", "abnormal_flag": true}
            ]
        }

    ``recent_vitals`` is populated only when the matching test names are found.
    ``raw_lab_results`` contains all rows for richer prompt context in the
    future.

    An empty snapshot dict is returned on error.

    Parameters
    ----------
    user_id:
        UUID of the user.
    client:
        Optional Supabase client; defaults to the global singleton.
    max_results:
        Max number of lab result rows to fetch.
    """
    if not user_id:
        return {}

    db = client or get_supabase_client()

    # ── 1. Fetch the most recent report date for this user ────────────────────
    last_checkup_date: Optional[str] = None
    try:
        rep_resp = (
            db.table("medical_reports")
            .select("report_date")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rep_rows = rep_resp.data or []
        if rep_rows and rep_rows[0].get("report_date"):
            last_checkup_date = str(rep_rows[0]["report_date"])
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "fetch_user_lab_snapshot: report date query failed for user_id=%s: %s",
            user_id,
            exc,
        )

    # ── 2. Fetch structured lab results (most recent report first) ────────────
    raw_labs: List[Dict[str, Any]] = []
    try:
        # Join: lab_results.report_id → medical_reports.id, filter by user_id.
        lab_resp = (
            db.table("lab_results")
            .select(
                "test_name, value, unit, reference_range, abnormal_flag, "
                "medical_reports!inner(user_id, created_at)"
            )
            .eq("medical_reports.user_id", user_id)
            .limit(max_results)
            .execute()
        )
        raw_labs = lab_resp.data or []
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "fetch_user_lab_snapshot: lab results query failed for user_id=%s: %s",
            user_id,
            exc,
        )

    # ── 3. Extract vitals from structured labs ────────────────────────────────
    #
    # The lab_results table stores heart rate, BP, and SpO2 as atomic rows with
    # standard test names (e.g. "Heart Rate", "Blood Pressure Systolic").
    # We scan them here for the context builder's recent_vitals block.

    _VITAL_MAP: Dict[str, str] = {
        "heart rate":                   "heart_rate",
        "blood pressure systolic":      "blood_pressure_systolic",
        "systolic blood pressure":      "blood_pressure_systolic",
        "blood pressure diastolic":     "blood_pressure_diastolic",
        "diastolic blood pressure":     "blood_pressure_diastolic",
        "spo2":                         "spo2_percentage",
        "oxygen saturation":            "spo2_percentage",
        "pulse oximetry":               "spo2_percentage",
    }

    vitals: Dict[str, Any] = {}
    for row in raw_labs:
        name_lower = (row.get("test_name") or "").lower().strip()
        key = _VITAL_MAP.get(name_lower)
        if key and key not in vitals and row.get("value") is not None:
            vitals[key] = row["value"]

    # Strip the nested join ghost columns before returning (keep it clean)
    clean_labs = [
        {k: v for k, v in row.items() if k != "medical_reports"}
        for row in raw_labs
    ]

    return {
        "last_checkup_date": last_checkup_date,
        "known_conditions": [],      # populated by future profile/condition table
        "recent_vitals": vitals,
        "raw_lab_results": clean_labs,
    }


# ── User profile stub ─────────────────────────────────────────────────────────

def fetch_user_profile(
    user_id: str,
    *,
    client: Optional[Client] = None,
) -> Dict[str, Any]:
    """Fetch user demographic profile.

    Currently returns a minimal stub (``user_id`` only) because the users/
    profiles table is not yet defined in the schema.  This function is the
    single integration point — once the table is added, only this function
    needs to change.

    Returns
    -------
    dict
        Keys: ``user_id``, (optionally) ``name``, ``age``, ``gender``,
        ``weight_kg``, ``height_cm``.
    """
    if not user_id:
        return {}

    # Stub: user_profiles table does not exist yet.
    # Once the table is created (via a migration), replace this with a real query.
    return {"user_id": user_id}
