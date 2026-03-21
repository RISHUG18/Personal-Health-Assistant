"""User management controller — business logic for user CRUD operations."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from supabase import Client

from backend.config.supabase_client import get_supabase_client
from backend.models.user import UserCreate, UserUpdate, User

logger = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    """Raised when a user is not found in the database."""

    pass


class UserAlreadyExistsError(Exception):
    """Raised when attempting to create a user with duplicate email."""

    pass


def create_user(user_data: UserCreate, client: Optional[Client] = None) -> User:
    """Create a new user in the database.

    Parameters
    ----------
    user_data:
        User creation data (validated Pydantic model).
    client:
        Supabase client instance (optional, defaults to global client).

    Returns
    -------
    User
        The newly created user with database-generated fields.

    Raises
    ------
    UserAlreadyExistsError
        If a user with the same email already exists.
    RuntimeError
        If database insertion fails.
    """
    if client is None:
        client = get_supabase_client()

    # Check if user with email already exists
    existing = (
        client.table("users")
        .select("id")
        .eq("email", user_data.email)
        .limit(1)
        .execute()
    )

    if existing.data:
        raise UserAlreadyExistsError(
            f"User with email '{user_data.email}' already exists"
        )

    # Prepare user row for insertion
    user_id = str(uuid.uuid4())
    now = datetime.utcnow()

    user_row = {
        "id": user_id,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "phone": user_data.phone,
        "date_of_birth": user_data.date_of_birth.isoformat()
        if user_data.date_of_birth
        else None,
        "gender": user_data.gender,
        # Address
        "address_line1": user_data.address_line1,
        "address_line2": user_data.address_line2,
        "city": user_data.city,
        "state": user_data.state,
        "postal_code": user_data.postal_code,
        "country": user_data.country,
        # Medical
        "blood_group": user_data.blood_group,
        "height_cm": user_data.height_cm,
        "weight_kg": user_data.weight_kg,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "is_active": True,
    }

    try:
        response = client.table("users").insert(user_row).execute()
        if not response.data:
            raise RuntimeError("No data returned from user creation")

        logger.info("Created user with ID: %s, email: %s", user_id, user_data.email)
        return User(**response.data[0])
    except Exception as exc:
        logger.error("Failed to create user: %s", exc)
        raise RuntimeError(f"Database error during user creation: {exc}") from exc


def get_user_by_id(user_id: str, client: Optional[Client] = None) -> User:
    """Fetch a user by their UUID.

    Parameters
    ----------
    user_id:
        UUID of the user to retrieve.
    client:
        Supabase client instance (optional).

    Returns
    -------
    User
        The user with the given ID.

    Raises
    ------
    UserNotFoundError
        If no user with the given ID exists.
    RuntimeError
        If database query fails.
    """
    if client is None:
        client = get_supabase_client()

    try:
        response = (
            client.table("users")
            .select("*")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            raise UserNotFoundError(f"User with ID '{user_id}' not found")

        return User(**response.data[0])
    except UserNotFoundError:
        raise
    except Exception as exc:
        logger.error("Failed to fetch user by ID: %s", exc)
        raise RuntimeError(f"Database error: {exc}") from exc


def get_user_by_email(email: str, client: Optional[Client] = None) -> User:
    """Fetch a user by their email address.

    Parameters
    ----------
    email:
        Email address of the user.
    client:
        Supabase client instance (optional).

    Returns
    -------
    User
        The user with the given email.

    Raises
    ------
    UserNotFoundError
        If no user with the given email exists.
    RuntimeError
        If database query fails.
    """
    if client is None:
        client = get_supabase_client()

    try:
        response = (
            client.table("users")
            .select("*")
            .eq("email", email)
            .limit(1)
            .execute()
        )

        if not response.data:
            raise UserNotFoundError(f"User with email '{email}' not found")

        return User(**response.data[0])
    except UserNotFoundError:
        raise
    except Exception as exc:
        logger.error("Failed to fetch user by email: %s", exc)
        raise RuntimeError(f"Database error: {exc}") from exc


def update_user(
    user_id: str, user_data: UserUpdate, client: Optional[Client] = None
) -> User:
    """Update an existing user's information.

    Parameters
    ----------
    user_id:
        UUID of the user to update.
    user_data:
        User update data (only non-None fields will be updated).
    client:
        Supabase client instance (optional).

    Returns
    -------
    User
        The updated user.

    Raises
    ------
    UserNotFoundError
        If no user with the given ID exists.
    RuntimeError
        If database update fails.
    """
    if client is None:
        client = get_supabase_client()

    # Verify user exists
    get_user_by_id(user_id, client)

    # Build update dict (only include non-None fields)
    update_data = {}
    for field, value in user_data.model_dump(exclude_unset=True).items():
        if field == "date_of_birth" and value is not None:
            update_data[field] = value.isoformat()
        else:
            update_data[field] = value

    if not update_data:
        # No fields to update, return existing user
        return get_user_by_id(user_id, client)

    update_data["updated_at"] = datetime.utcnow().isoformat()

    try:
        response = (
            client.table("users")
            .update(update_data)
            .eq("id", user_id)
            .execute()
        )

        if not response.data:
            raise RuntimeError("No data returned from user update")

        logger.info("Updated user with ID: %s", user_id)
        return User(**response.data[0])
    except Exception as exc:
        logger.error("Failed to update user: %s", exc)
        raise RuntimeError(f"Database error during user update: {exc}") from exc


def delete_user(user_id: str, client: Optional[Client] = None) -> None:
    """Delete a user from the database.

    This will cascade delete all related data (medical_reports, alerts, etc.)
    due to foreign key constraints.

    Parameters
    ----------
    user_id:
        UUID of the user to delete.
    client:
        Supabase client instance (optional).

    Raises
    ------
    UserNotFoundError
        If no user with the given ID exists.
    RuntimeError
        If database deletion fails.
    """
    if client is None:
        client = get_supabase_client()

    # Verify user exists
    get_user_by_id(user_id, client)

    try:
        client.table("users").delete().eq("id", user_id).execute()
        logger.info("Deleted user with ID: %s", user_id)
    except Exception as exc:
        logger.error("Failed to delete user: %s", exc)
        raise RuntimeError(f"Database error during user deletion: {exc}") from exc


def update_last_login(user_id: str, client: Optional[Client] = None) -> None:
    """Update the last_login_at timestamp for a user.

    Parameters
    ----------
    user_id:
        UUID of the user.
    client:
        Supabase client instance (optional).

    Raises
    ------
    RuntimeError
        If database update fails.
    """
    if client is None:
        client = get_supabase_client()

    try:
        client.table("users").update(
            {"last_login_at": datetime.utcnow().isoformat()}
        ).eq("id", user_id).execute()

        logger.debug("Updated last_login_at for user: %s", user_id)
    except Exception as exc:
        logger.warning("Failed to update last_login_at: %s", exc)
        # Don't raise - this is a non-critical operation
