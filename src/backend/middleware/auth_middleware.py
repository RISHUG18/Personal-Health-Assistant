"""Authentication middleware for FastAPI using Supabase."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.config.supabase_client import get_supabase_client

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Validate JWT token using Supabase Auth and return the user_id (UUID).
    
    This middleware extracts the Bearer token, passes it to Supabase's
    get_user(), which verifies the token signature over the network or locally,
    and returns the authenticated user's ID.
    """
    token = credentials.credentials
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
