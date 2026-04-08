"""Doctor dashboard API routes.

Endpoints
---------
GET /api/v1/doctor/patients
    List all patients assigned to the logged-in doctor.

POST /api/v1/doctor/patients
    Add a patient to the doctor's roster (create mapping).

DELETE /api/v1/doctor/patients/{patient_id}
    Remove a patient from the doctor's roster (delete mapping).

GET /api/v1/doctor/patients/{patient_id}/summary
    Comprehensive patient overview (profile, reports, alerts, summaries, vitals).

GET /api/v1/doctor/patients/{patient_id}/reports
    All medical reports for a patient with lab result counts.

GET /api/v1/doctor/patients/{patient_id}/reports/{report_id}
    Full report detail with all extracted lab results.

GET /api/v1/doctor/patients/{patient_id}/alerts
    All alerts with evidence for a patient.

POST /api/v1/doctor/patients/{patient_id}/evaluate-alerts
    Manually trigger rules-engine alert evaluation for a patient.

GET /api/v1/doctor/patients/{patient_id}/lab-results
    All lab results across all reports, grouped by report.

Authorization
-------------
Every endpoint uses ``get_current_user_with_role`` to validate the JWT and
fetch the user's role.  Access is denied (403) if:
- The caller's role is not ``'doctor'``
- The doctor is not mapped to the requested patient (via ``doctor_patient_mapping``)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.middleware.auth_middleware import get_current_user_with_role
from backend.controllers.doctor_controller import (
    DoctorNotAuthorizedError,
    MappingAlreadyExistsError,
    MappingNotFoundError,
    PatientNotFoundError,
    ReportNotFoundError,
    add_patient,
    evaluate_patient_alerts,
    get_doctor_patients,
    get_patient_alerts,
    get_patient_lab_results,
    get_patient_report_detail,
    get_patient_reports,
    get_patient_summary,
    remove_patient,
)
from backend.services.summaries.generator import SummaryGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/doctor", tags=["doctor"])
_summary_generator: SummaryGenerator | None = None


# ── Request Models ───────────────────────────────────────────────────────────

class AddPatientRequest(BaseModel):
    """Request body for POST /api/v1/doctor/patients."""
    patient_id: str = Field(..., description="UUID of the patient to assign to this doctor")


class EvaluateAlertsRequest(BaseModel):
    """Optional request body for POST evaluate-alerts."""
    location: str | None = Field(None, description="Location for environmental modifiers")
    date: str | None = Field(None, description="Date override for evaluation (ISO format)")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _require_doctor(current_user: dict) -> str:
    """Extract doctor_id from the authenticated user, enforcing role=doctor.

    Parameters
    ----------
    current_user:
        Dict with ``id`` and ``role`` from ``get_current_user_with_role``.

    Returns
    -------
    str
        The doctor's user UUID.

    Raises
    ------
    HTTPException 403
        If the user is not a doctor.
    """
    if current_user.get("role") != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can access this endpoint.",
        )
    return current_user["id"]


def _get_summary_generator() -> SummaryGenerator:
    """Lazily create a shared summary generator for doctor-triggered runs."""
    global _summary_generator
    if _summary_generator is None:
        _summary_generator = SummaryGenerator()
    return _summary_generator


# ── GET /api/v1/doctor/patients ──────────────────────────────────────────────

@router.get("/patients", status_code=status.HTTP_200_OK)
async def list_patients(
    current_user: dict = Depends(get_current_user_with_role),
):
    """List all patients assigned to the authenticated doctor.

    Returns a list of patient profiles with:
    - Basic info (name, age, gender, contact)
    - Risk level derived from active alerts (``high``/``medium``/``low``)
    - Alert counts broken down by severity
    - Report count and last report date
    - Assignment date

    Patients are sorted by risk level (highest first), then alphabetically.
    """
    doctor_id = _require_doctor(current_user)

    try:
        patients = get_doctor_patients(doctor_id)
    except Exception as exc:
        logger.error("Failed to fetch patients for doctor %s: %s", doctor_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch patients: {exc}",
        ) from exc

    return {
        "doctor_id": doctor_id,
        "count": len(patients),
        "patients": patients,
    }


# ── POST /api/v1/doctor/patients ─────────────────────────────────────────────

@router.post("/patients", status_code=status.HTTP_201_CREATED)
async def add_patient_route(
    body: AddPatientRequest,
    current_user: dict = Depends(get_current_user_with_role),
):
    """Add a patient to the doctor's roster.

    Creates a ``doctor_patient_mapping`` row linking the authenticated
    doctor to the specified patient.  The patient must exist and have
    ``role='patient'``.
    """
    doctor_id = _require_doctor(current_user)

    try:
        result = add_patient(doctor_id, body.patient_id)
    except PatientNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except MappingAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error(
            "Failed to add patient %s for doctor %s: %s",
            body.patient_id, doctor_id, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add patient: {exc}",
        ) from exc

    return result


# ── DELETE /api/v1/doctor/patients/{patient_id} ──────────────────────────────

@router.delete("/patients/{patient_id}", status_code=status.HTTP_200_OK)
async def remove_patient_route(
    patient_id: str,
    current_user: dict = Depends(get_current_user_with_role),
):
    """Remove a patient from the doctor's roster.

    Deletes the ``doctor_patient_mapping`` row.  This does NOT delete
    the patient's data — it only removes the doctor's access.
    """
    doctor_id = _require_doctor(current_user)

    try:
        result = remove_patient(doctor_id, patient_id)
    except MappingNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error(
            "Failed to remove patient %s for doctor %s: %s",
            patient_id, doctor_id, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove patient: {exc}",
        ) from exc

    return result


# ── GET /api/v1/doctor/patients/{patient_id}/summary ─────────────────────────

@router.get("/patients/{patient_id}/summary", status_code=status.HTTP_200_OK)
async def patient_summary(
    patient_id: str,
    current_user: dict = Depends(get_current_user_with_role),
):
    """Comprehensive overview for a single patient.

    Returns:
    - **patient**: Full profile with computed age
    - **reports**: Total count + 5 most recent reports
    - **alerts**: Severity breakdown + 3 most recent alerts
    - **latest_health_summary**: Most recent doctor-facing AI summary
    - **wearable_vitals**: 7-day aggregated wearable metrics
    """
    doctor_id = _require_doctor(current_user)

    try:
        summary = get_patient_summary(doctor_id, patient_id)
    except DoctorNotAuthorizedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except PatientNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error(
            "Failed to fetch summary for patient %s (doctor %s): %s",
            patient_id, doctor_id, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch patient summary: {exc}",
        ) from exc

    return summary


# ── GET /api/v1/doctor/patients/{patient_id}/reports ─────────────────────────

@router.get("/patients/{patient_id}/reports", status_code=status.HTTP_200_OK)
async def patient_reports(
    patient_id: str,
    current_user: dict = Depends(get_current_user_with_role),
):
    """List all medical reports for a patient.

    Each report includes:
    - Report metadata (date, type, file name, URL)
    - Processing status
    - Lab results count
    """
    doctor_id = _require_doctor(current_user)

    try:
        reports = get_patient_reports(doctor_id, patient_id)
    except DoctorNotAuthorizedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error(
            "Failed to fetch reports for patient %s (doctor %s): %s",
            patient_id, doctor_id, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch patient reports: {exc}",
        ) from exc

    return {
        "patient_id": patient_id,
        "count": len(reports),
        "reports": reports,
    }


# ── GET /api/v1/doctor/patients/{patient_id}/reports/{report_id} ─────────────

@router.get(
    "/patients/{patient_id}/reports/{report_id}",
    status_code=status.HTTP_200_OK,
)
async def patient_report_detail(
    patient_id: str,
    report_id: str,
    current_user: dict = Depends(get_current_user_with_role),
):
    """Full detail of a single medical report.

    Includes:
    - Complete report metadata
    - OCR extracted text
    - All extracted lab results with values, units, and abnormal flags
    """
    doctor_id = _require_doctor(current_user)

    try:
        report = get_patient_report_detail(doctor_id, patient_id, report_id)
    except DoctorNotAuthorizedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ReportNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error(
            "Failed to fetch report %s for patient %s (doctor %s): %s",
            report_id, patient_id, doctor_id, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch report detail: {exc}",
        ) from exc

    return report


# ── GET /api/v1/doctor/patients/{patient_id}/alerts ──────────────────────────

@router.get("/patients/{patient_id}/alerts", status_code=status.HTTP_200_OK)
async def patient_alerts(
    patient_id: str,
    current_user: dict = Depends(get_current_user_with_role),
):
    """All alerts for a patient with full evidence.

    Each alert includes:
    - Severity, reason, creation timestamp
    - Evidence linking to specific lab results and OCR snippets
    """
    doctor_id = _require_doctor(current_user)

    try:
        alerts_data = get_patient_alerts(doctor_id, patient_id)
    except DoctorNotAuthorizedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error(
            "Failed to fetch alerts for patient %s (doctor %s): %s",
            patient_id, doctor_id, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch patient alerts: {exc}",
        ) from exc

    return alerts_data


# ── POST /api/v1/doctor/patients/{patient_id}/evaluate-alerts ────────────────

@router.post(
    "/patients/{patient_id}/evaluate-alerts",
    status_code=status.HTTP_200_OK,
)
async def evaluate_alerts_route(
    patient_id: str,
    body: EvaluateAlertsRequest | None = None,
    current_user: dict = Depends(get_current_user_with_role),
):
    """Manually trigger the rules engine for a patient.

    Runs the same 13-rule deterministic evaluation that the nightly cron
    executes, but on demand.  The operation is **idempotent** — re-running
    replaces previously stored alerts.

    Optionally accepts ``location`` and ``date`` for environmental
    severity modifiers.
    """
    doctor_id = _require_doctor(current_user)
    location = body.location if body else None
    date_str = body.date if body else None

    try:
        result = evaluate_patient_alerts(
            doctor_id, patient_id,
            location=location,
            date_str=date_str,
        )
    except DoctorNotAuthorizedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error(
            "Alert evaluation failed for patient %s (doctor %s): %s",
            patient_id, doctor_id, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Alert evaluation failed: {exc}",
        ) from exc

    return result


# ── POST /api/v1/doctor/patients/{patient_id}/generate-summary ──────────────

@router.post(
    "/patients/{patient_id}/generate-summary",
    status_code=status.HTTP_201_CREATED,
)
async def generate_summary_route(
    patient_id: str,
    current_user: dict = Depends(get_current_user_with_role),
):
    """Generate fresh AI summaries for a doctor-assigned patient."""
    doctor_id = _require_doctor(current_user)

    try:
        # Reuse the existing doctor-patient authorization check before
        # allowing a manual summary generation from the dashboard.
        get_patient_summary(doctor_id, patient_id)
        result = _get_summary_generator().generate_weekly_summaries(user_id=patient_id)
    except DoctorNotAuthorizedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except PatientNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error(
            "Summary generation failed for patient %s (doctor %s): %s",
            patient_id, doctor_id, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summary generation failed: {exc}",
        ) from exc

    return {
        "status": "ok" if not result.get("errors") else "partial",
        "user_id": patient_id,
        "generated": result.get("generated", []),
        "errors": result.get("errors", []),
    }


# ── GET /api/v1/doctor/patients/{patient_id}/lab-results ─────────────────────

@router.get(
    "/patients/{patient_id}/lab-results",
    status_code=status.HTTP_200_OK,
)
async def patient_lab_results(
    patient_id: str,
    current_user: dict = Depends(get_current_user_with_role),
):
    """All lab results for a patient, grouped by report.

    Provides a consolidated view of every extracted lab value across all
    of the patient's uploaded medical reports.  Useful for tracking trends
    across multiple reports over time.
    """
    doctor_id = _require_doctor(current_user)

    try:
        result = get_patient_lab_results(doctor_id, patient_id)
    except DoctorNotAuthorizedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error(
            "Failed to fetch lab results for patient %s (doctor %s): %s",
            patient_id, doctor_id, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch lab results: {exc}",
        ) from exc

    return result
