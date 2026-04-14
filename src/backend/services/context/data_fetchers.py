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

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from supabase import Client

from backend.config.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


def _normalise_city(city: Optional[str]) -> Optional[str]:
    """Return a canonical city string for safe equality checks.

    Normalisation trims leading/trailing whitespace, collapses repeated
    internal spaces, and lowercases the value.  ``None`` and empty strings
    return ``None``.
    """
    if not city:
        return None
    compact = " ".join(city.strip().split())
    return compact.lower() if compact else None


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
            .order("report_date", desc=True)
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

def _calculate_age(date_of_birth: str | None) -> int | None:
    """Return whole years since *date_of_birth* (ISO-8601 string), or None."""
    if not date_of_birth:
        return None
    try:
        dob = date.fromisoformat(str(date_of_birth))
        today = date.today()
        # Subtract one year if the birthday hasn't occurred yet this year.
        return (
            today.year - dob.year
            - ((today.month, today.day) < (dob.month, dob.day))
        )
    except (ValueError, TypeError) as exc:
        logger.debug("_calculate_age: could not parse date_of_birth=%r: %s", date_of_birth, exc)
        return None


def fetch_user_profile(
    user_id: str,
    *,
    client: Optional[Client] = None,
) -> Dict[str, Any]:
    """Fetch user demographic profile from the ``users`` table.

    Queries ``full_name``, ``date_of_birth``, ``gender``, ``weight_kg``, and
    ``height_cm``.  Age is **calculated** from ``date_of_birth`` at query time
    rather than reading the now-dropped redundant ``age`` column.

    Returns
    -------
    dict
        Keys: ``user_id``, (optionally) ``name``, ``age`` (int, calculated),
        ``gender``, ``weight_kg``, ``height_cm``.
    """
    if not user_id:
        return {}

    db = client or get_supabase_client()
    try:
        response = (
            db.table("users")
            .select("full_name, date_of_birth, gender, weight_kg, height_cm")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            return {"user_id": user_id}

        row = rows[0]
        profile: Dict[str, Any] = {"user_id": user_id}

        if row.get("full_name") is not None:
            profile["name"] = row["full_name"]

        # Calculate age from date_of_birth — never read the dropped ``age`` column.
        age = _calculate_age(row.get("date_of_birth"))
        if age is not None:
            profile["age"] = age

        if row.get("gender") is not None:
            profile["gender"] = row["gender"]
        if row.get("weight_kg") is not None:
            profile["weight_kg"] = row["weight_kg"]
        if row.get("height_cm") is not None:
            profile["height_cm"] = row["height_cm"]

        return profile
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "fetch_user_profile failed for user_id=%s: %s", user_id, exc
        )
        return {"user_id": user_id}


# ── Cached environmental data ──────────────────────────────────────────────────

def fetch_cached_environment(
    user_id: str,
    *,
    current_lat: Optional[float] = None,
    current_lon: Optional[float] = None,
    movement_threshold_deg: float = 0.08,
    current_gps_city: Optional[str] = None,
    city: Optional[str] = None,
    client: Optional[Client] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieve the most recent cached environmental snapshot for *user_id*.

    This is a **read-only** helper — it never calls any external API.  It is
    useful when the caller wants to display the last-known environmental
    context without triggering a new Open-Meteo fetch (e.g. for historical
    queries or when the user has no city configured).

    The returned dict has the same shape as
    :meth:`~backend.services.environment.models.EnvironmentalSnapshot.to_context_dict`
    so it can be passed directly to
    :func:`~backend.services.context.context_builder.build_context` as the
    ``environment`` argument.

    Parameters
    ----------
    user_id:
        UUID of the user.
    current_lat:
        Optional current latitude from the client GPS.
    current_lon:
        Optional current longitude from the client GPS.
    movement_threshold_deg:
        Degree threshold for cache invalidation.  Default ``0.05`` is roughly
        5–6 km depending on latitude and is sufficient for AQI/weather-zone
        cache safety.
    current_gps_city:
        Optional live GPS-derived city from the mobile client.  When provided,
        this is used only as a secondary fallback check when coordinates are
        not available.
    city:
        Optional city filter.  When supplied, only rows ``WHERE
        location_city = city`` are considered.  Useful when a user has data
        for multiple cities.
    client:
        Optional Supabase client; defaults to the global singleton.

    Returns
    -------
    dict or None
        Dict with keys ``location_city``, ``aqi_level``,
        ``temperature_celsius``, ``weather_condition``; or ``None`` when no
        cached entry exists or on query failure.
    """
    if not user_id:
        return None

    db = client or get_supabase_client()
    try:
        query = (
            db.table("environmental_data")
            .select(
                "location_city, latitude, longitude, temperature_celsius, "
                "humidity_percent, aqi_level, weather_condition, recorded_at"
            )
            .eq("user_id", user_id)
            .order("recorded_at", desc=True)
            .limit(1)
        )
        if city:
            query = query.eq("location_city", city)

        response = query.execute()
        rows = response.data or []
        if not rows:
            return None

        row = rows[0]

        # Safety net (primary): coordinate distance check.
        # If the user moved beyond the threshold, invalidate cache.
        cached_lat = row.get("latitude")
        cached_lon = row.get("longitude")
        if (
            current_lat is not None
            and current_lon is not None
            and cached_lat is not None
            and cached_lon is not None
        ):
            lat_diff = abs(float(cached_lat) - float(current_lat))
            lon_diff = abs(float(cached_lon) - float(current_lon))
            if lat_diff > movement_threshold_deg or lon_diff > movement_threshold_deg:
                logger.info(
                    "Invalidating cached environment for user_id=%s due to "
                    "coordinate drift (lat_diff=%.5f, lon_diff=%.5f, "
                    "threshold=%.5f).",
                    user_id,
                    lat_diff,
                    lon_diff,
                    movement_threshold_deg,
                )
                return None

        # Safety net (secondary fallback): city check only when coordinates are
        # not available on the request.
        cached_city = _normalise_city(row.get("location_city"))
        live_city = _normalise_city(current_gps_city)
        if current_lat is None and current_lon is None and live_city and cached_city and live_city != cached_city:
            logger.info(
                "Invalidating cached environment for user_id=%s due to city "
                "mismatch (cached='%s', live='%s').",
                user_id,
                row.get("location_city"),
                current_gps_city,
            )
            return None

        return {
            "location_city":       row.get("location_city"),
            "aqi_level":           row.get("aqi_level"),
            "temperature_celsius": row.get("temperature_celsius"),
            "weather_condition":   row.get("weather_condition"),
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "fetch_cached_environment failed for user_id=%s: %s", user_id, exc
        )
        return None


# ── Wearable vitals ───────────────────────────────────────────────────────────

def fetch_wearable_vitals(
    user_id: str,
    *,
    days: int = 7,
) -> Optional[Dict[str, Any]]:
    """Fetch an aggregated wearable vitals summary for *user_id*.

    Uses the :class:`~backend.services.wearable.WearableService` singleton to
    compute avg / min / max / latest for each metric over the last *days* days,
    then converts it to the context-builder-ready dict via
    :meth:`~backend.services.wearable.models.VitalsSummary.to_context_dict`.

    Returns ``None`` (rather than an empty dict) when the user has no wearable
    data, so the caller's ``if wearable_data:`` guard works correctly.

    Parameters
    ----------
    user_id:
        UUID of the user.
    days:
        Aggregation window in days (default: 7).
    """
    if not user_id:
        return None

    try:
        from backend.services.wearable import get_wearable_service  # local import to avoid circular
        service = get_wearable_service()
        summary = service.get_vitals_summary(user_id=user_id, days=days)
        if not summary.metrics:
            return None
        return summary.to_context_dict()
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "fetch_wearable_vitals failed for user_id=%s: %s", user_id, exc
        )
        return None


def _coerce_optional_int(value: Any) -> Optional[int]:
    """Best-effort numeric coercion used by wearable trend array formatting."""
    if value is None:
        return None
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def _empty_wearable_gap_filled_arrays(days: int, dates: List[str]) -> Dict[str, Any]:
    """Return the canonical gap-filled wearable structure with all-null metrics."""
    return {
        "timeframe_days": days,
        "dates": dates,
        "heart_rate": {
            "min": [None] * len(dates),
            "max": [None] * len(dates),
            "avg": [None] * len(dates),
        },
        "sleep_minutes": [None] * len(dates),
        "spo2_avg": [None] * len(dates),
        "total_steps": [None] * len(dates),
    }


async def fetch_wearable_gap_filled_arrays(
    supabase_client,
    user_id: str,
    days: int = 7,
) -> Dict[str, Any]:
    """Fetch daily wearable aggregates and fill missing calendar dates with ``None``.

    This function is intended for LLM-facing temporal reasoning. It:

    1. Generates a perfect calendar window covering the last ``days`` up to today.
    2. Calls the ``get_daily_wearable_aggregates`` Supabase RPC on a worker
       thread so the FastAPI event loop is never blocked by the synchronous
       Supabase client.
    3. Re-shapes the sparse DB rows into parallel arrays with explicit gaps.

    Parameters
    ----------
    supabase_client:
        Live Supabase client used to execute the RPC.
    user_id:
        UUID of the user whose wearable trend window is requested.
    days:
        Lookback window in whole days, inclusive of today.

    Returns
    -------
    dict
        Gap-filled arrays ready for LLM context, e.g. ``dates``,
        ``heart_rate.min``, ``sleep_minutes``, ``spo2_avg``, ``total_steps``.
        On error, returns the same shape with all metric values set to ``None``.
    """
    if not user_id:
        return _empty_wearable_gap_filled_arrays(0, [])

    window_days = max(int(days or 7), 1)
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=window_days - 1)
    all_dates = [
        (start_date + timedelta(days=offset)).isoformat()
        for offset in range(window_days)
    ]
    empty_payload = _empty_wearable_gap_filled_arrays(window_days, all_dates)

    def _call_rpc() -> List[Dict[str, Any]]:
        response = supabase_client.rpc(
            "get_daily_wearable_aggregates",
            {"p_user_id": user_id, "p_days": window_days},
        ).execute()
        return response.data or []

    try:
        rows: List[Dict[str, Any]] = await asyncio.to_thread(_call_rpc)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "fetch_wearable_gap_filled_arrays RPC failed for user_id=%s days=%s: %s",
            user_id,
            window_days,
            exc,
        )
        return empty_payload

    rows_by_date: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        raw_record_date = row.get("record_date")
        if not raw_record_date:
            continue

        if isinstance(raw_record_date, date):
            record_key = raw_record_date.isoformat()
        else:
            record_key = str(raw_record_date)[:10]

        rows_by_date[record_key] = row

    formatted = {
        "timeframe_days": window_days,
        "dates": all_dates,
        "heart_rate": {"min": [], "max": [], "avg": []},
        "sleep_minutes": [],
        "spo2_avg": [],
        "total_steps": [],
    }

    for iso_date in all_dates:
        row = rows_by_date.get(iso_date)
        formatted["heart_rate"]["min"].append(
            _coerce_optional_int(row.get("hr_min")) if row else None
        )
        formatted["heart_rate"]["max"].append(
            _coerce_optional_int(row.get("hr_max")) if row else None
        )
        formatted["heart_rate"]["avg"].append(
            _coerce_optional_int(row.get("hr_avg")) if row else None
        )
        formatted["sleep_minutes"].append(
            _coerce_optional_int(row.get("sleep_minutes")) if row else None
        )
        formatted["spo2_avg"].append(
            _coerce_optional_int(row.get("spo2_avg")) if row else None
        )
        formatted["total_steps"].append(
            _coerce_optional_int(row.get("steps_total")) if row else None
        )

    return formatted


# ── Longitudinal lab trends ───────────────────────────────────────────────────

async def fetch_trended_labs(
    supabase_client,
    user_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """Fetch the 3 most recent readings for every canonical lab test a patient has.

    Calls the ``get_trended_labs`` Postgres RPC (migration
    ``018_add_get_trended_labs_rpc.sql``) which uses a window function to rank
    each test's history chronologically and returns only the top-3 rows per
    test.

    The raw rows are grouped into a dict keyed by ``test_name`` so the LLM
    context builder can iterate over tests directly.

    Parameters
    ----------
    supabase_client:
        A live Supabase :class:`~supabase.Client` instance.  Accepting it as a
        parameter (rather than calling ``get_supabase_client()`` internally)
        keeps the function testable without patching globals.
    user_id:
        UUID of the patient whose lab history is fetched.

    Returns
    -------
    dict
        Mapping of ``canonical_test_name -> list[{date, value, unit}]``.
        Each inner list contains up to 3 entries, ordered newest-first.
        Returns an empty dict on error or when no data exists.

    Example
    -------
    ::

        {
            "Fasting Blood Sugar": [
                {"date": "2026-04-01", "value": 105, "unit": "mg/dL"},
                {"date": "2025-10-15", "value": 112, "unit": "mg/dL"}
            ],
            "Hemoglobin A1c": [
                {"date": "2026-04-01", "value": 6.2, "unit": "%"}
            ]
        }
    """
    from collections import defaultdict

    if not user_id:
        return {}

    def _call_rpc() -> List[Dict[str, Any]]:
        response = supabase_client.rpc(
            "get_trended_labs",
            {"p_user_id": user_id},
        ).execute()
        return response.data or []

    try:
        rows: List[Dict[str, Any]] = await asyncio.to_thread(_call_rpc)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "fetch_trended_labs RPC failed for user_id=%s: %s", user_id, exc
        )
        return {}

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        test_name = row.get("test_name")
        if not test_name:
            continue
        grouped[test_name].append(
            {
                "date":  str(row["record_date"]) if row.get("record_date") else None,
                "value": row.get("test_value"),
                "unit":  row.get("unit"),
            }
        )

    return dict(grouped)
