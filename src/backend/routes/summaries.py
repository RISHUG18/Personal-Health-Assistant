"""Health summaries API routes.

Endpoints
---------
POST /api/v1/summaries/generate/{target_user_id}
    Trigger timeframe-specific summary generation for a specific patient.
    Supports either:
    - Service-role token (cron automation).
    - Authenticated end user triggering generation for their own user_id.

GET /api/v1/summaries/{target_user_id}
    Retrieve stored summaries with role-based authorization.
    Patients see their own user-facing summaries.
    Doctors see doctor-facing summaries for their mapped patients.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.config.supabase_client import get_supabase_client
from backend.middleware.auth_middleware import (
    get_current_user,
    get_current_user_with_role,
)
from backend.services.summaries import SummaryGenerator, SummaryTimeframe

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/summaries", tags=["summaries"])
_optional_bearer = HTTPBearer(auto_error=False)

# Process-level singleton — avoids recreating GeminiService per request.
_generator: Optional[SummaryGenerator] = None


def _get_generator() -> SummaryGenerator:
    """Lazy-init the SummaryGenerator singleton."""
    global _generator
    if _generator is None:
        _generator = SummaryGenerator()
    return _generator


# ── POST: generate summaries (service-role or self-user JWT) ─────────────────

def _is_service_role_token(token: str) -> bool:
    """Return True if bearer token matches the configured service-role key."""
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    return bool(service_key) and token == service_key


def _authorize_summary_generation(
    target_user_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),
) -> dict:
    """Authorize generation caller and return caller context.

    Returns
    -------
    dict
        ``{"caller_type": "service" | "user", "requester_id": str | None}``
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    if _is_service_role_token(token):
        return {"caller_type": "service", "requester_id": None}

    # Use the standard user dependency logic for JWT validation.
    requester_id = get_current_user(credentials)
    if requester_id != target_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only trigger summary generation for your own account.",
        )

    return {"caller_type": "user", "requester_id": requester_id}

@router.post(
    "/generate/{target_user_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Generate timeframe-specific summaries for a patient",
)
async def generate_summaries(
    target_user_id: str,
    timeframe: SummaryTimeframe | None = Query(
        default=None,
        description=(
            "Summary timeframe to generate: weekly, monthly, or quarterly. "
            "Defaults to weekly (7 days) for patient self-requests."
        ),
    ),
    auth_context: dict = Depends(_authorize_summary_generation),
):
    """Trigger summary generation for a single patient.

    Authorization:
    - Service-role token can trigger generation for any patient (cron/admin).
    - Standard JWT users can trigger generation only for their own user_id.

    Generates both 'user' and 'doctor' summaries and persists them to the
    ``health_summaries`` table.
    """
    caller_type = auth_context["caller_type"]
    effective_timeframe = timeframe

    # Patient-triggered requests should default to 7-day summaries.
    if effective_timeframe is None:
        if caller_type == "user":
            effective_timeframe = SummaryTimeframe.WEEKLY
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="timeframe query parameter is required for service-role requests.",
            )

    generator = _get_generator()

    try:
        result = await generator.generate_weekly_summaries(
            user_id=target_user_id,
            timeframe=effective_timeframe,
        )
    except Exception as exc:
        logger.error(
            "Summary generation failed for user_id=%s timeframe=%s: %s",
            target_user_id,
            effective_timeframe.value,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summary generation failed: {exc}",
        ) from exc

    # Report partial failures (e.g., one role succeeded, the other didn't).
    if result.get("errors"):
        logger.warning(
            "Partial failure generating summaries for user_id=%s timeframe=%s: %s",
            target_user_id,
            effective_timeframe.value,
            result["errors"],
        )

    return {
        "status": "ok" if not result.get("errors") else "partial",
        "user_id": target_user_id,
        "timeframe": effective_timeframe.value,
        "triggered_by": caller_type,
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
    timeframe: SummaryTimeframe = Query(
        default=SummaryTimeframe.WEEKLY,
        description="Summary timeframe to retrieve: weekly, monthly, or quarterly.",
    ),
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
            .eq("period_type", timeframe.value)
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
        "timeframe": timeframe.value,
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
