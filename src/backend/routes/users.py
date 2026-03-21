"""User management API routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from backend.controllers.users_controller import (
    UserAlreadyExistsError,
    UserNotFoundError,
    create_user,
    delete_user,
    get_user_by_email,
    get_user_by_id,
    update_user,
)
from backend.models.user import UserCreate, UserResponse, UserUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_new_user(user_data: UserCreate) -> UserResponse:
    """Create a new user.

    Parameters
    ----------
    user_data:
        User creation data.

    Returns
    -------
    UserResponse
        The newly created user.

    Raises
    ------
    HTTPException
        409 if user with email already exists.
        500 if database error occurs.
    """
    try:
        user = create_user(user_data)
        return UserResponse(**user.model_dump())
    except UserAlreadyExistsError as exc:
        logger.warning("Attempted to create duplicate user: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Failed to create user: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {exc}",
        ) from exc


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str) -> UserResponse:
    """Get a user by ID.

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


@router.get("/email/{email}", response_model=UserResponse)
def get_user_by_email_route(email: str) -> UserResponse:
    """Get a user by email address.

    Parameters
    ----------
    email:
        Email address of the user to retrieve.

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
    try:
        user = get_user_by_email(email)
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


@router.patch("/{user_id}", response_model=UserResponse)
def update_user_route(user_id: str, user_data: UserUpdate) -> UserResponse:
    """Update a user's information.

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


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def delete_user_route(user_id: str) -> dict:
    """Delete a user.

    This will cascade delete all related data (medical reports, alerts, etc.).

    Parameters
    ----------
    user_id:
        UUID of the user to delete.

    Raises
    ------
    HTTPException
        404 if user not found.
        500 if database error occurs.
    """
    try:
        delete_user(user_id)
        return {"message": "User deleted successfully", "user_id": user_id}
    except UserNotFoundError as exc:
        logger.warning("User not found: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Failed to delete user: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {exc}",
        ) from exc
