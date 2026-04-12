"""HTTP routes for fetching and evaluating alerts.

Endpoints
---------
GET /alerts/{user_id}
    Fetch all stored alerts for a user (JWT-protected).

POST /alerts/evaluate/{user_id}
    Run the rules engine for the authenticated user (JWT-protected).

POST /alerts/admin/evaluate/{user_id}
    Run the rules engine for any user — **service-role only**.
    Called by the nightly cron automation script.
"""
import logging
from dataclasses import dataclass
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status

from backend.config.supabase_client import get_supabase_client
from backend.middleware.auth_middleware import get_current_user, verify_service_role
from backend.rules.definitions import RULES_CONFIG
from backend.rules.models import AlertRecord, Severity
from backend.services.wearable import get_wearable_service

router = APIRouter(prefix="/alerts", tags=["alerts"])
logger = logging.getLogger(__name__)

# Tri-state capability cache for deployments that have not applied the
# environmental_evidence column migration yet.
_ALERT_EVIDENCE_HAS_ENV_COLUMN: bool | None = None


@dataclass
class _WearableEvidence:
    report_id: str | None = None
    lab_result_id: str | None = None
    ocr_snippet: str | None = None


def _format_wearable_evidence(metric_type: str, value: float, unit: str | None, summary: dict) -> str:
    unit_label = unit or summary.get("unit") or ""
    avg = summary.get("avg")
    min_val = summary.get("min")
    max_val = summary.get("max")
    return (
        f"wearable:{metric_type} value={value} {unit_label} "
        f"(avg={avg}, min={min_val}, max={max_val})"
    )


def _pick_metric_value(summary: dict) -> float | None:
    latest = summary.get("latest")
    if latest is not None:
        return float(latest)
    avg = summary.get("avg")
    return float(avg) if avg is not None else None


def _parse_iso_date(value: object) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            return None
    return None


def _build_wearable_alert(
    *,
    metric_type: str,
    severity: Severity,
    reason: str,
    evidence: _WearableEvidence,
) -> AlertRecord:
    return AlertRecord(
        rule_id=f"wearable_{metric_type}",
        triggered=True,
        severity=severity,
        reason=reason,
        evidence=[evidence],
    )


def _evaluate_wearable_alerts(user_id: str) -> list[AlertRecord]:
    config = RULES_CONFIG.get("wearable", {})
    sleep_cfg = RULES_CONFIG.get("sleep_activity", {})
    cardio_cfg = RULES_CONFIG.get("cardio_vitals", {})
    if not (config or sleep_cfg or cardio_cfg):
        return []

    service = get_wearable_service()
    summary = service.get_vitals_summary(user_id=user_id, days=7)
    metrics = {m.metric_type: {
        "avg": m.avg_value,
        "min": m.min_value,
        "max": m.max_value,
        "latest": m.latest_value,
        "unit": m.unit,
    } for m in summary.metrics}

    alerts: list[AlertRecord] = []

    def add_low_high_alert(metric: str, label: str, low_medium: float | None, low_high: float | None,
                           high_medium: float | None = None, high_high: float | None = None) -> None:
        metric_summary = metrics.get(metric)
        if not metric_summary:
            return
        value = _pick_metric_value(metric_summary)
        if value is None:
            return

        severity: Severity | None = None
        reason: str | None = None

        if low_medium is not None and value < low_medium:
            severity = Severity.HIGH if (low_high is not None and value < low_high) else Severity.MEDIUM
            reason = f"Low {label}: {value}"
        if high_medium is not None and value > high_medium:
            high_sev = Severity.HIGH if (high_high is not None and value > high_high) else Severity.MEDIUM
            high_reason = f"High {label}: {value}"
            if severity is None:
                severity = high_sev
                reason = high_reason
            else:
                # Prefer the more severe condition if both sides trigger
                if high_sev == Severity.HIGH:
                    severity = high_sev
                    reason = high_reason

        if severity and reason:
            evidence = _WearableEvidence(
                ocr_snippet=_format_wearable_evidence(metric, value, metric_summary.get("unit"), metric_summary)
            )
            alerts.append(_build_wearable_alert(
                metric_type=metric,
                severity=severity,
                reason=f"{reason} {metric_summary.get('unit') or ''}".strip(),
                evidence=evidence,
            ))

    def add_low_only_alert(metric: str, label: str, low_medium: float | None, low_high: float | None,
                           critical_low: float | None = None) -> None:
        metric_summary = metrics.get(metric)
        if not metric_summary:
            return
        value = _pick_metric_value(metric_summary)
        if value is None or low_medium is None:
            return

        if value >= low_medium:
            return

        severity = Severity.MEDIUM
        if critical_low is not None and value < critical_low:
            severity = Severity.HIGH
        elif low_high is not None and value < low_high:
            severity = Severity.HIGH

        evidence = _WearableEvidence(
            ocr_snippet=_format_wearable_evidence(metric, value, metric_summary.get("unit"), metric_summary)
        )
        alerts.append(_build_wearable_alert(
            metric_type=metric,
            severity=severity,
            reason=f"Low {label}: {value} {metric_summary.get('unit') or ''}".strip(),
            evidence=evidence,
        ))

    heart_rate = config.get("heart_rate", {})
    if cardio_cfg.get("heart_rate"):
        merged = {**cardio_cfg.get("heart_rate", {}), **heart_rate}
        heart_rate = merged
    add_low_high_alert(
        "heart_rate",
        "heart rate",
        heart_rate.get("low_medium"),
        heart_rate.get("low_high"),
        heart_rate.get("high_medium"),
        heart_rate.get("high_high"),
    )

    resting_hr = config.get("resting_heart_rate", {})
    add_low_high_alert(
        "resting_heart_rate",
        "resting heart rate",
        resting_hr.get("low_medium"),
        resting_hr.get("low_high"),
        resting_hr.get("high_medium"),
        resting_hr.get("high_high"),
    )

    spo2 = config.get("spo2", {})
    add_low_only_alert(
        "spo2",
        "SpO2",
        spo2.get("low_medium"),
        spo2.get("low_high"),
        spo2.get("critical_low"),
    )

    hrv = config.get("hrv_ms", {})
    add_low_only_alert(
        "hrv_ms",
        "HRV",
        hrv.get("low_medium"),
        hrv.get("low_high"),
        None,
    )

    steps = config.get("steps", {})
    if steps:
        add_low_only_alert(
            "steps",
            "daily steps",
            steps.get("daily_low_medium"),
            steps.get("daily_low_high"),
            None,
        )

    sleep_minutes = config.get("sleep_minutes", {})
    if sleep_minutes:
        add_low_high_alert(
            "sleep_minutes",
            "sleep duration (minutes)",
            sleep_minutes.get("low_medium"),
            sleep_minutes.get("low_high"),
            sleep_minutes.get("high_medium"),
            None,
        )

    deep_sleep = config.get("deep_sleep_minutes", {})
    add_low_only_alert(
        "deep_sleep_minutes",
        "deep sleep (minutes)",
        deep_sleep.get("low_medium"),
        deep_sleep.get("low_high"),
        None,
    )

    calories = config.get("calories_burned", {})
    add_low_only_alert(
        "calories_burned",
        "calories burned",
        calories.get("low_medium"),
        calories.get("low_high"),
        None,
    )

    sleep_score = config.get("sleep_score", {})
    add_low_only_alert(
        "sleep_score",
        "sleep score",
        sleep_score.get("low_medium"),
        sleep_score.get("low_high"),
        None,
    )

    if sleep_cfg:
        sleep_rules = sleep_cfg.get("sleep", {})
        steps_rules = sleep_cfg.get("steps", {})

        def count_consecutive_days(metric_type: str, threshold: float, aggregator: str) -> int:
            readings = service.get_raw_readings(user_id, metric_type, days=14, limit=2000)
            if not readings:
                return 0
            by_day: dict[date, list[float]] = {}
            for row in readings:
                day = _parse_iso_date(row.get("recorded_at"))
                if not day:
                    continue
                by_day.setdefault(day, []).append(float(row.get("value") or 0))

            days_sorted = sorted(by_day.keys(), reverse=True)
            streak = 0
            for day in days_sorted:
                values = by_day.get(day, [])
                if not values:
                    break
                if aggregator == "sum":
                    daily = sum(values)
                elif aggregator == "avg":
                    daily = sum(values) / len(values)
                else:
                    daily = max(values)
                if daily < threshold:
                    streak += 1
                else:
                    break
            return streak

        sleep_hours_low = sleep_rules.get("hours_low")
        sleep_hours_high = sleep_rules.get("hours_high")
        if sleep_hours_low:
            streak = count_consecutive_days("sleep_minutes", sleep_hours_low * 60, "sum")
            if streak >= sleep_rules.get("consecutive_days_medium", 0):
                severity = Severity.HIGH if sleep_hours_high and streak >= sleep_rules.get("consecutive_days_high", 0) else Severity.MEDIUM
                reason = f"Low sleep duration for {streak} days (avg < {sleep_hours_low}h)"
                evidence = _WearableEvidence(ocr_snippet=f"sleep_minutes streak={streak} days")
                alerts.append(_build_wearable_alert(
                    metric_type="sleep_minutes",
                    severity=severity,
                    reason=reason,
                    evidence=evidence,
                ))

        steps_low = steps_rules.get("daily_low")
        steps_critical = steps_rules.get("daily_medium")
        if steps_low:
            streak = count_consecutive_days("steps", steps_low, "sum")
            if streak >= steps_rules.get("consecutive_days_medium", 0):
                severity = Severity.HIGH if steps_critical and streak >= steps_rules.get("consecutive_days_medium", 0) else Severity.MEDIUM
                reason = f"Low steps for {streak} days (daily < {steps_low})"
                evidence = _WearableEvidence(ocr_snippet=f"steps streak={streak} days")
                alerts.append(_build_wearable_alert(
                    metric_type="steps",
                    severity=severity,
                    reason=reason,
                    evidence=evidence,
                ))

    if cardio_cfg.get("blood_pressure"):
        bp_cfg = cardio_cfg.get("blood_pressure", {})
        systolic = bp_cfg.get("systolic", {})
        diastolic = bp_cfg.get("diastolic", {})

        def add_bp_alert(metric_type: str, label: str, cfg: dict) -> None:
            metric_summary = metrics.get(metric_type)
            if not metric_summary:
                return
            value = _pick_metric_value(metric_summary)
            if value is None:
                return
            low_high = cfg.get("low_high")
            medium_high = cfg.get("medium_high")
            critical_high = cfg.get("critical_high")
            if medium_high is None:
                return
            if value < medium_high:
                return
            if critical_high is not None and value >= critical_high:
                severity = Severity.HIGH
                label_prefix = "Critical"
            elif value >= medium_high:
                severity = Severity.MEDIUM
                label_prefix = "High"
            else:
                severity = Severity.LOW
                label_prefix = "Elevated"
            reason = f"{label_prefix} {label}: {value}"
            evidence = _WearableEvidence(
                ocr_snippet=_format_wearable_evidence(metric_type, value, metric_summary.get("unit"), metric_summary)
            )
            alerts.append(_build_wearable_alert(
                metric_type=metric_type,
                severity=severity,
                reason=reason,
                evidence=evidence,
            ))

        add_bp_alert("blood_pressure_systolic", "systolic blood pressure", systolic)
        add_bp_alert("blood_pressure_diastolic", "diastolic blood pressure", diastolic)

    return alerts


def _fetch_alert_evidence_rows(client, alert_ids: list[str]) -> list[dict]:
    """Fetch alert evidence with compatibility for older DB schemas."""
    global _ALERT_EVIDENCE_HAS_ENV_COLUMN

    if _ALERT_EVIDENCE_HAS_ENV_COLUMN is False:
        fallback = (
            client.table("alert_evidence")
            .select("id, alert_id, report_id, lab_result_id, ocr_text_snippet")
            .in_("alert_id", alert_ids)
            .execute()
        )
        return fallback.data or []

    try:
        response = (
            client.table("alert_evidence")
            .select(
                "id, alert_id, report_id, lab_result_id, "
                "ocr_text_snippet, environmental_evidence"
            )
            .in_("alert_id", alert_ids)
            .execute()
        )
        _ALERT_EVIDENCE_HAS_ENV_COLUMN = True
        return response.data or []
    except Exception as exc:
        message = str(exc)
        missing_env_column = (
            "PGRST204" in message
            or (
                "environmental_evidence" in message
                and (
                    "does not exist" in message
                    or "schema cache" in message
                    or "Could not find" in message
                )
            )
        )
        if not missing_env_column:
            raise

        _ALERT_EVIDENCE_HAS_ENV_COLUMN = False
        logger.info(
            "alert_evidence.environmental_evidence is missing; "
            "falling back to legacy evidence query: %s",
            exc,
        )
        fallback = (
            client.table("alert_evidence")
            .select("id, alert_id, report_id, lab_result_id, ocr_text_snippet")
            .in_("alert_id", alert_ids)
            .execute()
        )
        return fallback.data or []


# ---------------------------------------------------------------------------
# GET /alerts/{user_id}  — fetch all alerts for a user
# ---------------------------------------------------------------------------

@router.get("/{user_id}", status_code=status.HTTP_200_OK)
async def get_alerts(user_id: str, include_evidence: bool = True, current_user: str = Depends(get_current_user)):
    if user_id != current_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    """Return all alerts stored in the database for a given user.

    Alerts are generated by the deterministic rules engine (run separately
    via ``POST /alerts/evaluate``) and persisted into the ``alerts`` table.

    Query parameters:
    - ``include_evidence`` (default: ``true``) — when true, each alert
      includes its ``evidence`` list from the ``alert_evidence`` table,
      linking the alert back to the specific lab result rows and OCR
      snippets that triggered it.

    Response shape:
    ```json
    {
      "user_id": "...",
      "count": 3,
      "alerts": [
        {
          "id": "...",
          "severity": "high",
          "reason": "...",
          "created_at": "...",
          "evidence": [
            {
              "id": "...",
              "report_id": "...",
              "lab_result_id": "...",
              "ocr_text_snippet": "..."
            }
          ]
        }
      ]
    }
    ```
    """
    client = get_supabase_client()

    # Fetch alerts for this user, most-recent first.
    try:
        alerts_resp = (
            client.table("alerts")
            .select("id, severity, reason, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch alerts: {exc}",
        ) from exc

    alerts = alerts_resp.data or []

    if not alerts:
        return {"user_id": user_id, "count": 0, "alerts": []}

    # Optionally attach evidence rows for each alert.
    if include_evidence:
        alert_ids = [a["id"] for a in alerts]
        try:
            evidence_rows = _fetch_alert_evidence_rows(client, alert_ids)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch alert evidence: {exc}",
            ) from exc

        # Group evidence rows by alert_id.
        evidence_by_alert: dict[str, list[dict]] = {}
        for ev in evidence_rows:
            aid = ev["alert_id"]
            evidence_by_alert.setdefault(aid, []).append(
                {
                    "id": ev["id"],
                    "report_id": ev.get("report_id"),
                    "lab_result_id": ev.get("lab_result_id"),
                    "ocr_text_snippet": ev.get("ocr_text_snippet"),
                    "environmental_evidence": ev.get("environmental_evidence"),
                }
            )

        for alert in alerts:
            alert["evidence"] = evidence_by_alert.get(alert["id"], [])

    return {"user_id": user_id, "count": len(alerts), "alerts": alerts}


# ---------------------------------------------------------------------------
# Shared evaluation logic (DRY helper — used by both endpoints below)
# ---------------------------------------------------------------------------

def _run_evaluation(user_id: str, location: str | None, date: str | None) -> dict:
    """Shared evaluation logic used by both user and admin endpoints.

    Extracted to satisfy the DRY principle — both routes delegate here.
    """
    client = get_supabase_client()

    try:
        from backend.rules.engine import evaluate_rules
        from backend.rules.inserter import persist_alerts
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rules engine not available: {exc}",
        ) from exc

    try:
        alerts = evaluate_rules(client=client, user_id=user_id, location=location, date=date)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rules evaluation failed: {exc}",
        ) from exc

    try:
        wearable_alerts = _evaluate_wearable_alerts(user_id)
        alerts.extend(wearable_alerts)
    except Exception as exc:
        logger.warning("Wearable alert evaluation failed for user_id=%s: %s", user_id, exc)

    try:
        result = persist_alerts(client=client, user_id=user_id, alerts=alerts)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Persisting alerts failed: {exc}",
        ) from exc

    return {
        "user_id": user_id,
        "alerts_triggered": len(alerts),
        "deleted": result.get("deleted", 0),
        "inserted": result.get("inserted", 0),
        "evidence_inserted": result.get("evidence_inserted", 0),
        "errors": result.get("errors", []),
    }


# ---------------------------------------------------------------------------
# POST /alerts/evaluate/{user_id}  — run rules engine (JWT-protected)
# ---------------------------------------------------------------------------

@router.post("/evaluate/{user_id}", status_code=status.HTTP_200_OK)
async def evaluate_alerts(user_id: str, location: str | None = None, date: str | None = None, current_user: str = Depends(get_current_user)):
    """Run the deterministic rules engine for the authenticated user.

    Fetches all lab results for the user from ``lab_results`` (joined via
    ``medical_reports``), evaluates all 13 rules, deletes any previously
    stored alerts for the user, and inserts the new results.

    The operation is **idempotent** — re-running replaces old alerts.

    Returns a summary of what was stored.
    """
    if user_id != current_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return _run_evaluation(user_id, location, date)


# ---------------------------------------------------------------------------
# POST /alerts/admin/evaluate/{user_id}  — service-role only (cron / admin)
# ---------------------------------------------------------------------------

@router.post(
    "/admin/evaluate/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Run rules engine for a user (service-role only)",
)
async def admin_evaluate_alerts(
    user_id: str,
    location: str | None = None,
    date: str | None = None,
    _authorized: bool = Depends(verify_service_role),
):
    """Service-role-protected evaluation endpoint for the nightly cron job.

    Identical to ``POST /alerts/evaluate/{user_id}`` but secured via the
    ``SUPABASE_SERVICE_ROLE_KEY`` instead of a user JWT.  This allows the
    cron script to evaluate rules for *any* patient without impersonation.
    """
    return _run_evaluation(user_id, location, date)
