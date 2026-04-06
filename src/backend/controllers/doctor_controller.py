"""Doctor dashboard controller — business logic for doctor-facing operations.

Provides read-only queries for doctors to view their assigned patients'
profiles, reports, lab results, alerts, and health summaries.  Every function
verifies the doctor → patient mapping before returning data.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from backend.config.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


# ── Custom Exceptions ────────────────────────────────────────────────────────

class DoctorNotAuthorizedError(Exception):
    """Raised when the caller is not a doctor or not assigned to the patient."""
    pass


class PatientNotFoundError(Exception):
    """Raised when the requested patient does not exist."""
    pass


class ReportNotFoundError(Exception):
    """Raised when the requested report does not exist."""
    pass


# ── Internal Helpers ─────────────────────────────────────────────────────────

def _verify_mapping(doctor_id: str, patient_id: str, client=None) -> None:
    """Assert that a doctor → patient mapping exists.

    Raises
    ------
    DoctorNotAuthorizedError
        If the mapping row is absent.
    """
    if client is None:
        client = get_supabase_client()
    resp = (
        client.table("doctor_patient_mapping")
        .select("doctor_id")
        .eq("doctor_id", doctor_id)
        .eq("patient_id", patient_id)
        .limit(1)
        .execute()
    )
    if not resp.data:
        raise DoctorNotAuthorizedError(
            f"Doctor {doctor_id} is not assigned to patient {patient_id}."
        )


def _calculate_age(dob: Optional[str]) -> Optional[int]:
    """Return age in years from a date-of-birth ISO string, or None."""
    if not dob:
        return None
    try:
        born = date.fromisoformat(str(dob))
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    except (ValueError, TypeError):
        return None


def _highest_severity(alerts: List[Dict]) -> str:
    """Return the highest severity among a list of alert dicts."""
    order = {"high": 3, "medium": 2, "low": 1}
    best = "low"
    for a in alerts:
        sev = a.get("severity", "low")
        if order.get(sev, 0) > order.get(best, 0):
            best = sev
    return best


# ── Public API ───────────────────────────────────────────────────────────────

def get_doctor_patients(doctor_id: str) -> List[Dict[str, Any]]:
    """Return all patients assigned to the doctor with profile and risk info.

    Parameters
    ----------
    doctor_id:
        UUID of the authenticated doctor.

    Returns
    -------
    list[dict]
        Each dict contains patient profile info, report count, alert counts,
        and a derived ``risk_level``.
    """
    client = get_supabase_client()

    # 1. Get all patient IDs mapped to this doctor.
    mapping_resp = (
        client.table("doctor_patient_mapping")
        .select("patient_id, created_at")
        .eq("doctor_id", doctor_id)
        .execute()
    )
    mappings = mapping_resp.data or []
    if not mappings:
        return []

    patient_ids = [m["patient_id"] for m in mappings]
    mapping_dates = {m["patient_id"]: m["created_at"] for m in mappings}

    # 2. Fetch patient profiles.
    patients_resp = (
        client.table("users")
        .select("id, full_name, email, gender, date_of_birth, phone, city, "
                "blood_group, is_active, last_login_at")
        .in_("id", patient_ids)
        .eq("role", "patient")
        .execute()
    )
    patients = patients_resp.data or []

    # 3. Fetch alert counts per patient (for risk calculation).
    alerts_resp = (
        client.table("alerts")
        .select("user_id, severity")
        .in_("user_id", patient_ids)
        .execute()
    )
    alerts_by_patient: Dict[str, List[Dict]] = {}
    for a in (alerts_resp.data or []):
        uid = a["user_id"]
        alerts_by_patient.setdefault(uid, []).append(a)

    # 4. Fetch report counts per patient.
    reports_resp = (
        client.table("medical_reports")
        .select("user_id, id, created_at")
        .in_("user_id", patient_ids)
        .execute()
    )
    report_counts: Dict[str, int] = {}
    last_report_date: Dict[str, str] = {}
    for r in (reports_resp.data or []):
        uid = r["user_id"]
        report_counts[uid] = report_counts.get(uid, 0) + 1
        existing = last_report_date.get(uid, "")
        if r.get("created_at", "") > existing:
            last_report_date[uid] = r["created_at"]

    # 5. Assemble response.
    result = []
    for p in patients:
        pid = p["id"]
        patient_alerts = alerts_by_patient.get(pid, [])
        high_count = sum(1 for a in patient_alerts if a.get("severity") == "high")
        medium_count = sum(1 for a in patient_alerts if a.get("severity") == "medium")

        # Derive risk_level from alerts.
        if high_count > 0:
            risk_level = "high"
        elif medium_count > 0:
            risk_level = "medium"
        else:
            risk_level = "low"

        result.append({
            "user_id": pid,
            "name": p.get("full_name", ""),
            "email": p.get("email", ""),
            "gender": p.get("gender"),
            "age": _calculate_age(p.get("date_of_birth")),
            "date_of_birth": p.get("date_of_birth"),
            "phone": p.get("phone"),
            "city": p.get("city"),
            "blood_group": p.get("blood_group"),
            "is_active": p.get("is_active", True),
            "risk_level": risk_level,
            "alert_counts": {
                "high": high_count,
                "medium": medium_count,
                "low": sum(1 for a in patient_alerts if a.get("severity") == "low"),
                "total": len(patient_alerts),
            },
            "report_count": report_counts.get(pid, 0),
            "last_report_at": last_report_date.get(pid),
            "last_login_at": p.get("last_login_at"),
            "assigned_at": mapping_dates.get(pid),
        })

    # Sort by risk_level descending (high first), then by name.
    order = {"high": 0, "medium": 1, "low": 2}
    result.sort(key=lambda x: (order.get(x["risk_level"], 3), x.get("name", "")))

    return result


def get_patient_summary(
    doctor_id: str,
    patient_id: str,
) -> Dict[str, Any]:
    """Return a comprehensive overview for a single patient.

    Includes profile, report count, alert summary, latest health summary,
    and recent wearable vitals.

    Raises
    ------
    DoctorNotAuthorizedError
        If the doctor is not mapped to this patient.
    PatientNotFoundError
        If the patient does not exist.
    """
    client = get_supabase_client()
    _verify_mapping(doctor_id, patient_id, client)

    # ── Profile ──────────────────────────────────────────────────────────
    user_resp = (
        client.table("users")
        .select("*")
        .eq("id", patient_id)
        .limit(1)
        .execute()
    )
    if not user_resp.data:
        raise PatientNotFoundError(f"Patient {patient_id} not found.")
    profile = user_resp.data[0]
    profile["age"] = _calculate_age(profile.get("date_of_birth"))

    # ── Reports overview ─────────────────────────────────────────────────
    reports_resp = (
        client.table("medical_reports")
        .select("id, report_date, report_type, source_file_name, created_at, processing_status")
        .eq("user_id", patient_id)
        .order("created_at", desc=True)
        .limit(5)
        .execute()
    )
    recent_reports = reports_resp.data or []

    total_reports_resp = (
        client.table("medical_reports")
        .select("id", count="exact")
        .eq("user_id", patient_id)
        .execute()
    )
    total_reports = total_reports_resp.count or 0

    # ── Alerts summary ───────────────────────────────────────────────────
    alerts_resp = (
        client.table("alerts")
        .select("id, severity, reason, created_at")
        .eq("user_id", patient_id)
        .order("created_at", desc=True)
        .execute()
    )
    alerts = alerts_resp.data or []

    alert_summary = {
        "total": len(alerts),
        "high": sum(1 for a in alerts if a.get("severity") == "high"),
        "medium": sum(1 for a in alerts if a.get("severity") == "medium"),
        "low": sum(1 for a in alerts if a.get("severity") == "low"),
        "recent": alerts[:3],  # last 3 alerts
    }

    # ── Latest doctor-facing health summary ──────────────────────────────
    try:
        summary_resp = (
            client.table("health_summaries")
            .select("id, period_type, target_role, summary_content, created_at")
            .eq("user_id", patient_id)
            .eq("target_role", "doctor")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        latest_summary = (summary_resp.data or [None])[0]
    except Exception as exc:
        logger.warning("Could not fetch health summary for patient %s: %s", patient_id, exc)
        latest_summary = None

    # ── Wearable vitals — recent 7-day snapshot ──────────────────────────
    vitals_snapshot = None
    try:
        from backend.services.wearable import get_wearable_service
        svc = get_wearable_service()
        vitals_summary = svc.get_vitals_summary(user_id=patient_id, days=7)
        vitals_snapshot = {
            m.metric_type: {
                "avg": m.avg_value,
                "min": m.min_value,
                "max": m.max_value,
                "latest": m.latest_value,
                "samples": m.sample_count,
                "unit": m.unit,
            }
            for m in vitals_summary.metrics
        }
    except Exception as exc:
        logger.warning("Could not fetch wearable vitals for patient %s: %s", patient_id, exc)

    return {
        "patient": profile,
        "reports": {
            "total": total_reports,
            "recent": recent_reports,
        },
        "alerts": alert_summary,
        "latest_health_summary": latest_summary,
        "wearable_vitals": vitals_snapshot,
    }


def get_patient_reports(
    doctor_id: str,
    patient_id: str,
) -> List[Dict[str, Any]]:
    """Return all medical reports for a patient with lab result counts.

    Raises
    ------
    DoctorNotAuthorizedError
        If the doctor is not mapped to this patient.
    """
    client = get_supabase_client()
    _verify_mapping(doctor_id, patient_id, client)

    reports_resp = (
        client.table("medical_reports")
        .select("id, user_id, report_date, report_type, source_file_name, "
                "source_url, ocr_confidence, created_at, processing_status")
        .eq("user_id", patient_id)
        .order("created_at", desc=True)
        .execute()
    )
    reports = reports_resp.data or []

    if not reports:
        return []

    report_ids = [r["id"] for r in reports]

    # Count lab results per report.
    lab_resp = (
        client.table("lab_results")
        .select("report_id, id")
        .in_("report_id", report_ids)
        .execute()
    )
    lab_counts: Dict[str, int] = {}
    for lr in (lab_resp.data or []):
        rid = lr["report_id"]
        lab_counts[rid] = lab_counts.get(rid, 0) + 1

    for r in reports:
        r["lab_results_count"] = lab_counts.get(r["id"], 0)

    return reports


def get_patient_report_detail(
    doctor_id: str,
    patient_id: str,
    report_id: str,
) -> Dict[str, Any]:
    """Return full detail of a single report including all lab results.

    Raises
    ------
    DoctorNotAuthorizedError
        If the doctor is not mapped to this patient.
    ReportNotFoundError
        If the report does not exist or does not belong to this patient.
    """
    client = get_supabase_client()
    _verify_mapping(doctor_id, patient_id, client)

    # Fetch report row.
    report_resp = (
        client.table("medical_reports")
        .select("id, user_id, report_date, report_type, source_file_name, "
                "source_url, ocr_text, ocr_engine, ocr_confidence, "
                "created_at, processing_status")
        .eq("id", report_id)
        .eq("user_id", patient_id)
        .limit(1)
        .execute()
    )
    if not report_resp.data:
        raise ReportNotFoundError(
            f"Report {report_id} not found for patient {patient_id}."
        )

    report = report_resp.data[0]

    # Fetch all lab results for this report.
    labs_resp = (
        client.table("lab_results")
        .select("id, test_name, value, unit, reference_range, "
                "abnormal_flag, extracted_from_page")
        .eq("report_id", report_id)
        .execute()
    )
    report["lab_results"] = labs_resp.data or []
    report["lab_results_count"] = len(report["lab_results"])

    return report


def get_patient_alerts(
    doctor_id: str,
    patient_id: str,
) -> Dict[str, Any]:
    """Return all alerts for a patient with full evidence.

    Raises
    ------
    DoctorNotAuthorizedError
        If the doctor is not mapped to this patient.
    """
    client = get_supabase_client()
    _verify_mapping(doctor_id, patient_id, client)

    # Fetch alerts.
    alerts_resp = (
        client.table("alerts")
        .select("id, severity, reason, created_at")
        .eq("user_id", patient_id)
        .order("created_at", desc=True)
        .execute()
    )
    alerts = alerts_resp.data or []

    if not alerts:
        return {"patient_id": patient_id, "count": 0, "alerts": []}

    # Fetch evidence for all alerts.
    alert_ids = [a["id"] for a in alerts]
    evidence_resp = (
        client.table("alert_evidence")
        .select("id, alert_id, report_id, lab_result_id, ocr_text_snippet")
        .in_("alert_id", alert_ids)
        .execute()
    )

    evidence_by_alert: Dict[str, List[Dict]] = {}
    for ev in (evidence_resp.data or []):
        aid = ev["alert_id"]
        evidence_by_alert.setdefault(aid, []).append({
            "id": ev["id"],
            "report_id": ev.get("report_id"),
            "lab_result_id": ev.get("lab_result_id"),
            "ocr_text_snippet": ev.get("ocr_text_snippet"),
        })

    for alert in alerts:
        alert["evidence"] = evidence_by_alert.get(alert["id"], [])

    return {
        "patient_id": patient_id,
        "count": len(alerts),
        "alerts": alerts,
    }


# ── Patient Management ───────────────────────────────────────────────────────

class MappingAlreadyExistsError(Exception):
    """Raised when a doctor-patient mapping already exists."""
    pass


class MappingNotFoundError(Exception):
    """Raised when trying to remove a mapping that doesn't exist."""
    pass


def add_patient(
    doctor_id: str,
    patient_id: str,
) -> Dict[str, Any]:
    """Create a doctor → patient mapping.

    Parameters
    ----------
    doctor_id:
        UUID of the authenticated doctor.
    patient_id:
        UUID of the patient to assign.

    Returns
    -------
    dict
        Confirmation with doctor_id, patient_id, and created_at.

    Raises
    ------
    PatientNotFoundError
        If the patient UUID doesn't exist or isn't a patient.
    MappingAlreadyExistsError
        If the mapping already exists.
    """
    client = get_supabase_client()

    # Verify the patient exists and is actually a patient.
    patient_resp = (
        client.table("users")
        .select("id, full_name, role")
        .eq("id", patient_id)
        .limit(1)
        .execute()
    )
    if not patient_resp.data:
        raise PatientNotFoundError(f"User {patient_id} not found.")
    patient = patient_resp.data[0]
    if patient.get("role") != "patient":
        raise PatientNotFoundError(
            f"User {patient_id} is not a patient (role='{patient.get('role')}')."
        )

    # Check if mapping already exists.
    existing_resp = (
        client.table("doctor_patient_mapping")
        .select("doctor_id")
        .eq("doctor_id", doctor_id)
        .eq("patient_id", patient_id)
        .limit(1)
        .execute()
    )
    if existing_resp.data:
        raise MappingAlreadyExistsError(
            f"Doctor {doctor_id} is already assigned to patient {patient_id}."
        )

    # Insert the mapping.
    client.table("doctor_patient_mapping").insert({
        "doctor_id": doctor_id,
        "patient_id": patient_id,
    }).execute()

    logger.info("Doctor %s assigned to patient %s (%s)", doctor_id, patient_id, patient["full_name"])

    return {
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "patient_name": patient["full_name"],
        "message": f"Patient '{patient['full_name']}' added successfully.",
    }


def remove_patient(
    doctor_id: str,
    patient_id: str,
) -> Dict[str, Any]:
    """Remove a doctor → patient mapping.

    Parameters
    ----------
    doctor_id:
        UUID of the authenticated doctor.
    patient_id:
        UUID of the patient to unassign.

    Returns
    -------
    dict
        Confirmation message.

    Raises
    ------
    MappingNotFoundError
        If the mapping doesn't exist.
    """
    client = get_supabase_client()

    # Verify the mapping exists before attempting delete.
    existing_resp = (
        client.table("doctor_patient_mapping")
        .select("doctor_id")
        .eq("doctor_id", doctor_id)
        .eq("patient_id", patient_id)
        .limit(1)
        .execute()
    )
    if not existing_resp.data:
        raise MappingNotFoundError(
            f"No mapping exists between doctor {doctor_id} and patient {patient_id}."
        )

    # Delete the mapping.
    client.table("doctor_patient_mapping").delete().eq(
        "doctor_id", doctor_id
    ).eq(
        "patient_id", patient_id
    ).execute()

    logger.info("Doctor %s removed patient %s from their roster.", doctor_id, patient_id)

    return {
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "message": "Patient removed from your roster successfully.",
    }


def evaluate_patient_alerts(
    doctor_id: str,
    patient_id: str,
    location: Optional[str] = None,
    date_str: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the rules engine for a patient (doctor-triggered).

    This allows doctors to manually trigger alert evaluation for their
    patients without waiting for the nightly cron job.

    Raises
    ------
    DoctorNotAuthorizedError
        If the doctor is not mapped to this patient.
    """
    client = get_supabase_client()
    _verify_mapping(doctor_id, patient_id, client)

    from backend.rules.engine import evaluate_rules
    from backend.rules.inserter import persist_alerts

    alerts = evaluate_rules(client=client, user_id=patient_id, location=location, date=date_str)
    result = persist_alerts(client=client, user_id=patient_id, alerts=alerts)

    logger.info(
        "Doctor %s triggered alert evaluation for patient %s: %d alerts",
        doctor_id, patient_id, len(alerts),
    )

    return {
        "patient_id": patient_id,
        "alerts_triggered": len(alerts),
        "deleted": result.get("deleted", 0),
        "inserted": result.get("inserted", 0),
        "evidence_inserted": result.get("evidence_inserted", 0),
        "errors": result.get("errors", []),
    }


def get_patient_lab_results(
    doctor_id: str,
    patient_id: str,
) -> Dict[str, Any]:
    """Return all lab results across all reports for a patient.

    Groups lab results by report for easy viewing.

    Raises
    ------
    DoctorNotAuthorizedError
        If the doctor is not mapped to this patient.
    """
    client = get_supabase_client()
    _verify_mapping(doctor_id, patient_id, client)

    # Fetch all reports for this patient.
    reports_resp = (
        client.table("medical_reports")
        .select("id, report_date, report_type, source_file_name, created_at")
        .eq("user_id", patient_id)
        .order("created_at", desc=True)
        .execute()
    )
    reports = reports_resp.data or []

    if not reports:
        return {"patient_id": patient_id, "total_lab_results": 0, "reports": []}

    report_ids = [r["id"] for r in reports]

    # Fetch all lab results.
    labs_resp = (
        client.table("lab_results")
        .select("id, report_id, test_name, value, unit, reference_range, "
                "abnormal_flag, extracted_from_page")
        .in_("report_id", report_ids)
        .execute()
    )
    all_labs = labs_resp.data or []

    # Group by report_id.
    labs_by_report: Dict[str, List[Dict]] = {}
    for lab in all_labs:
        rid = lab["report_id"]
        labs_by_report.setdefault(rid, []).append(lab)

    # Build response with labs nested under each report.
    result_reports = []
    for r in reports:
        rid = r["id"]
        report_labs = labs_by_report.get(rid, [])
        result_reports.append({
            **r,
            "lab_results": report_labs,
            "lab_results_count": len(report_labs),
        })

    return {
        "patient_id": patient_id,
        "total_lab_results": len(all_labs),
        "reports": result_reports,
    }
