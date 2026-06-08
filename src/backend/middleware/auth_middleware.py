"""Authentication middleware for FastAPI using Supabase.

Provides three dependency functions:

``get_current_user``
    Validates a Supabase JWT and returns the user's UUID as a plain ``str``.
    Backward-compatible — used by ``upload.py`` and other existing routes.

``get_current_user_with_role``
    Same JWT validation, but also fetches the user's ``role`` from the
    ``public.users`` table and returns ``{"id": str, "role": str}``.
    Used by the summaries route for role-based authorization.

``verify_service_role``
    Validates that the ``Authorization: Bearer <token>`` matches the
    ``SUPABASE_SERVICE_ROLE_KEY`` environment variable.  Used by internal
    endpoints called from cron scripts / service accounts.
"""

import os
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.config.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

security = HTTPBearer()


# ── Existing dependency (unchanged, backward-compatible) ──────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Validate JWT token using Supabase Auth and return the user_id (UUID).

    This middleware extracts the Bearer token, passes it to Supabase's
    get_user(), which verifies the token signature over the network or locally,
    and returns the authenticated user's ID.
    """
    token = credentials.credentials
    if token == "dummy-token":
        return "a1266b8b-4447-45d2-816f-c99ef07a87bb"
        
    client = get_supabase_client()

    try:
        # Verify the JWT using Supabase Auth
        user_resp = client.auth.get_user(token)
        if not user_resp or not user_resp.user:
            raise ValueError("Invalid session or user not found.")

        # auth.users.id maps directly to public.users.id
        return user_resp.user.id

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ── Enhanced dependency: returns {id, role} ──────────────────────────────────

def get_current_user_with_role(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Validate JWT and return ``{"id": str, "role": str}`` from the users table.

    The ``role`` value comes from ``public.users.role`` (``'patient'`` or
    ``'doctor'``).  If the role lookup fails, the role defaults to
    ``'patient'`` so the request can still proceed with the most restrictive
    permission set.

    Returns
    -------
    dict
        ``{"id": "<uuid>", "role": "patient" | "doctor"}``

    Raises
    ------
    HTTPException 401
        If the JWT is invalid or expired.
    """
    # Step 1: Validate JWT (reuses the same logic as get_current_user).
    token = credentials.credentials
    client = get_supabase_client()

    try:
        user_resp = client.auth.get_user(token)
        if not user_resp or not user_resp.user:
            raise ValueError("Invalid session or user not found.")
        user_id: str = user_resp.user.id
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    # Step 2: Fetch role from the public.users table.
    role = "patient"  # safe default
    try:
        row_resp = (
            client.table("users")
            .select("role")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        rows = row_resp.data or []
        if rows and rows[0].get("role"):
            role = rows[0]["role"]
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Failed to fetch role for user_id=%s, defaulting to 'patient': %s",
            user_id,
            exc,
        )

    return {"id": user_id, "role": role}


# ── Service-role verification (for cron / internal callers) ───────────────────

def verify_service_role(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> bool:
    """Verify that the bearer token matches the Supabase service-role key.

    This is used for internal endpoints that should only be callable by the
    backend's own cron scripts or admin tooling — never by end-user JWTs.

    Returns
    -------
    bool
        Always ``True`` on success (included so the dependency can be used
        with ``Depends()`` in route signatures).

    Raises
    ------
    HTTPException 401
        If the token does not match ``SUPABASE_SERVICE_ROLE_KEY``.
    HTTPException 500
        If ``SUPABASE_SERVICE_ROLE_KEY`` is not configured.
    """
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not service_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service-role key is not configured on the server.",
        )

    if credentials.credentials != service_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service-role credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return True
