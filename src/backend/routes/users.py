"""User management API routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from backend.middleware.auth_middleware import get_current_user

from backend.controllers.users_controller import (
    UserNotFoundError,
    get_user_by_id,
    update_user,
)
from backend.models.user import UserResponse, UserUpdate
from backend.services.privacy import (
    PrivacyOperationError,
    delete_user_account,
    export_user_data_bytes,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me/export", response_class=StreamingResponse)
def export_my_data(current_user: str = Depends(get_current_user)) -> StreamingResponse:
    """Export all stored user data as a JSON attachment."""
    try:
        payload = export_user_data_bytes(current_user)
    except PrivacyOperationError as exc:
        logger.warning("Failed to export user data for %s: %s", current_user, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Unexpected export failure for %s: %s", current_user, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export user data.",
        ) from exc

    filename = f"user-export-{current_user}.json"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(iter([payload]), media_type="application/json", headers=headers)


@router.delete("/me", status_code=status.HTTP_200_OK)
def delete_my_account(current_user: str = Depends(get_current_user)) -> dict:
    """Hard-delete the authenticated user's account and associated data."""
    try:
        result = delete_user_account(current_user)
        return {
            "message": "User account deleted successfully",
            **result,
        }
    except PrivacyOperationError as exc:
        logger.warning("Privacy delete failed for %s: %s", current_user, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Unexpected delete failure for %s: %s", current_user, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user account.",
        ) from exc


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: str = Depends(get_current_user)) -> UserResponse:
    """Get the authenticated user's own profile."""
    try:
        user = get_user_by_id(current_user)
        return UserResponse(**user.model_dump())
    except UserNotFoundError as exc:
        logger.warning("User not found: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Failed to get current user: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user: {exc}",
        ) from exc


@router.patch("/me", response_model=UserResponse)
def update_my_profile(user_data: UserUpdate, current_user: str = Depends(get_current_user)) -> UserResponse:
    """Update the authenticated user's own profile."""
    try:
        user = update_user(current_user, user_data)
        return UserResponse(**user.model_dump())
    except UserNotFoundError as exc:
        logger.warning("User not found: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Failed to update current user: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {exc}",
        ) from exc


@router.get("/{user_id}", response_model=UserResponse, include_in_schema=False)
def get_user_compat(user_id: str, current_user: str = Depends(get_current_user)) -> UserResponse:
    """Backward-compatible self-profile route.

    Parameters
    ----------
    user_id:
        UUID of the user to retrieve.

    Returns
    -------
    UserResponse
        The requested user.

    Raises
    ------
    HTTPException
        404 if user not found.
        500 if database error occurs.
    """
    if user_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access another user's profile",
        )
    try:
        user = get_user_by_id(user_id)
        return UserResponse(**user.model_dump())
    except UserNotFoundError as exc:
        logger.warning("User not found: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Failed to get user: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user: {exc}",
        ) from exc


@router.patch("/{user_id}", response_model=UserResponse, include_in_schema=False)
def update_user_route(user_id: str, user_data: UserUpdate, current_user: str = Depends(get_current_user)) -> UserResponse:
    """Backward-compatible self-profile update route.

    Parameters
    ----------
    user_id:
        UUID of the user to update.
    user_data:
        User update data (only non-null fields will be updated).

    Returns
    -------
    UserResponse
        The updated user.

    Raises
    ------
    HTTPException
        404 if user not found.
        500 if database error occurs.
    """
    if user_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update another user's profile",
        )
    try:
        user = update_user(user_id, user_data)
        return UserResponse(**user.model_dump())
    except UserNotFoundError as exc:
        logger.warning("User not found: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Failed to update user: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {exc}",
        ) from exc
