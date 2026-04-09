"""Authentication endpoints integrating Supabase Auth with the custom public.users table."""
from datetime import datetime, timezone
import logging

from typing import Optional
from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.config.supabase_client import get_supabase_client

_log = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

class UserRegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[Literal["male", "female", "other"]] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    role: str = "patient"

class UserLoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(req: UserRegisterRequest):
    """Register a new user in Supabase Auth and mirror to the custom users table."""
    if req.role not in ("patient", "doctor"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Role must be either 'patient' or 'doctor'"
        )

    client = get_supabase_client()
    
    # 1. Create user in Supabase Auth (Auto-Confirming using Admin API for robustness)
    try:
        user_resp = client.auth.admin.create_user({
            "email": req.email,
            "password": req.password,
            "email_confirm": True
        })
        user = user_resp.user
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registration failed in Auth")

    # 2. Insert into custom `users` table keeping the exact same UUID
    try:
        payload = {
            "id": user.id,
            "email": req.email,
            "full_name": req.full_name,
            "role": req.role,
        }
        if req.date_of_birth is not None:
            payload["date_of_birth"] = req.date_of_birth.isoformat()
        if req.gender is not None:
            payload["gender"] = req.gender
        if req.height_cm is not None:
            payload["height_cm"] = req.height_cm
        if req.weight_kg is not None:
            payload["weight_kg"] = req.weight_kg

        client.table("users").insert(payload).execute()
        _log.info("Registered and inserted user %s properly.", user.id)
    except Exception as exc:
        _log.error("Failed to map user %s into public schema: %s", user.id, exc)
        # Atomic Rollback: Remove the Auth footprint if the table mapping failed (RLS issues etc).
        try:
            client.auth.admin.delete_user(user.id)
        except Exception as cleanup_exc: # pragma: no cover
            _log.error("Failed to clean up orphaned Auth user %s: %s", user.id, cleanup_exc)
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to create user profile linked to authentication."
        ) from exc
        
    # 3. Retrieve Session for immediate login
    try:
        auth_resp = client.auth.sign_in_with_password({
            "email": req.email,
            "password": req.password
        })
        session = auth_resp.session
    except Exception:
        session = None
        
    return {
        "message": "User registered successfully",
        "user_id": user.id,
        "access_token": session.access_token if session else None,
        "refresh_token": session.refresh_token if session else None,
    }


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(req: UserLoginRequest):
    """Authenticate a user using Supabase and return JWT tokens."""
    client = get_supabase_client()
    
    # 1. Authenticate using Supabase
    try:
        auth_resp = client.auth.sign_in_with_password({
            "email": req.email,
            "password": req.password
        })
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Login failed: {exc}") from exc
        
    if not auth_resp.user or not auth_resp.session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        
    # 2. Update last_login_at in the custom `users` table
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        client.table("users").update({"last_login_at": now_iso}).eq("id", auth_resp.user.id).execute()
        _log.info("User %s logged in.", auth_resp.user.id)
    except Exception as exc:
        _log.warning("Failed to update last_login_at for %s: %s", auth_resp.user.id, exc)
        
    return {
        "message": "Login successful",
        "user_id": auth_resp.user.id,
        "access_token": auth_resp.session.access_token,
        "refresh_token": auth_resp.session.refresh_token,
    }
