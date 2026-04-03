"""Health summaries API routes.

Endpoints
---------
POST /api/v1/summaries/generate/{target_user_id}
    Trigger weekly summary generation for a specific patient.
    **Service-role only** — called by the cron automation script.

GET /api/v1/summaries/{target_user_id}
    Retrieve stored summaries with role-based authorization.
    Patients see their own user-facing summaries.
    Doctors see doctor-facing summaries for their mapped patients.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.config.supabase_client import get_supabase_client
from backend.middleware.auth_middleware import (
    get_current_user_with_role,
    verify_service_role,
)
from backend.services.summaries.generator import SummaryGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/summaries", tags=["summaries"])

# Process-level singleton — avoids recreating GeminiService per request.
_generator: Optional[SummaryGenerator] = None


def _get_generator() -> SummaryGenerator:
    """Lazy-init the SummaryGenerator singleton."""
    global _generator
    if _generator is None:
        _generator = SummaryGenerator()
    return _generator


# ── POST: generate summaries (service-role only) ─────────────────────────────

@router.post(
    "/generate/{target_user_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Generate weekly summaries for a patient",
)
async def generate_summaries(
    target_user_id: str,
    _authorized: bool = Depends(verify_service_role),
):
    """Trigger summary generation for a single patient.

    Secured via service-role key — only the cron script (or admin tooling)
    should call this endpoint.  Generates both 'user' and 'doctor' summaries
    and persists them to the ``health_summaries`` table.
    """
    generator = _get_generator()

    try:
        result = generator.generate_weekly_summaries(user_id=target_user_id)
    except Exception as exc:
        logger.error(
            "Summary generation failed for user_id=%s: %s",
            target_user_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summary generation failed: {exc}",
        ) from exc

    # Report partial failures (e.g., one role succeeded, the other didn't).
    if result.get("errors"):
        logger.warning(
            "Partial failure generating summaries for user_id=%s: %s",
            target_user_id,
            result["errors"],
        )

    return {
        "status": "ok" if not result.get("errors") else "partial",
        "user_id": target_user_id,
        "generated": result.get("generated", []),
        "errors": result.get("errors", []),
    }


# ── GET: retrieve summaries (JWT-protected) ──────────────────────────────────

@router.get(
    "/{target_user_id}",
    summary="Retrieve health summaries for a patient",
)
async def get_summaries(
    target_user_id: str,
    current_user: dict = Depends(get_current_user_with_role),
    role: Optional[str] = Query(
        default=None,
        description=(
            "Filter by target_role ('user' or 'doctor'). "
            "Patients are auto-forced to 'user'. "
            "Doctors default to 'doctor' but may request 'user' too."
        ),
    ),
    limit: int = Query(
        default=4,
        ge=1,
        le=10,
        description="Number of most recent summaries to return (max 10).",
    ),
):
    """Retrieve stored health summaries with role-based access control.

    Authorization rules
    -------------------
    **Patient** (``users.role = 'patient'``):
        - ``current_user.id`` must equal ``target_user_id``.
        - ``role`` query parameter is forced to ``'user'`` regardless of input.
        - 403 if requesting another patient's summaries.

    **Doctor** (``users.role = 'doctor'``):
        - Must have a row in ``doctor_patient_mapping`` linking to the patient.
        - May request ``role='user'`` or ``role='doctor'`` summaries.
        - 403 if not assigned to this patient.
    """
    requester_id: str = current_user["id"]
    requester_role: str = current_user["role"]

    # ── Authorization ─────────────────────────────────────────────────────────

    if requester_role == "patient":
        # Rule 1: patients can only access their own user-facing summaries.
        if requester_id != target_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own summaries.",
            )
        # Force the role to 'user' — patients must never see doctor summaries.
        role = "user"

    elif requester_role == "doctor":
        # Rule 2: doctors must be mapped to this patient.
        if not _doctor_is_assigned(requester_id, target_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this patient.",
            )
        # Default to doctor-facing summaries, but allow explicit 'user' too.
        if role is None:
            role = "doctor"

    else:
        # Unknown role — deny by default.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unrecognised user role.",
        )

    # ── Fetch from Supabase ───────────────────────────────────────────────────

    client = get_supabase_client()
    try:
        query = (
            client.table("health_summaries")
            .select("id, user_id, period_type, target_role, summary_content, created_at")
            .eq("user_id", target_user_id)
            .eq("target_role", role)
            .order("created_at", desc=True)
            .limit(limit)
        )
        response = query.execute()
        summaries = response.data or []
    except Exception as exc:
        logger.error(
            "Failed to fetch summaries for user_id=%s: %s",
            target_user_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve summaries.",
        ) from exc

    return {
        "user_id": target_user_id,
        "role": role,
        "count": len(summaries),
        "summaries": summaries,
    }


# ── Helpers ──────────────────────────────────────────────────────────────────

def _doctor_is_assigned(doctor_id: str, patient_id: str) -> bool:
    """Check whether a doctor → patient mapping exists."""
    client = get_supabase_client()
    try:
        resp = (
            client.table("doctor_patient_mapping")
            .select("doctor_id")
            .eq("doctor_id", doctor_id)
            .eq("patient_id", patient_id)
            .limit(1)
            .execute()
        )
        return bool(resp.data)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "doctor_patient_mapping lookup failed (doctor=%s, patient=%s): %s",
            doctor_id,
            patient_id,
            exc,
        )
        return False
