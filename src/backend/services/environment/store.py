"""Supabase-backed implementation of IEnvironmentStore.

Inserts a fully populated :class:`~backend.services.environment.models.EnvironmentalSnapshot`
into the ``environmental_data`` table defined in migration 005.

Design
------
* **Single Responsibility**: this module only writes to the DB.  It does not
  validate or transform data — that is the caller's job.
* **Dependency Inversion**: callers depend on
  :class:`~backend.services.environment.interfaces.IEnvironmentStore`;
  this concrete class is injected, never imported directly by callers.
* The ``save`` method is intentionally **best-effort**: it logs and swallows
  any DB error so that a write failure never propagates up to the user-facing
  RAG pipeline.

Table written
-------------
``environmental_data`` (see ``src/db/migrations/005_add_environmental_data.sql``)
"""

from __future__ import annotations

import logging
from typing import Optional

from supabase import Client

from backend.config.supabase_client import get_supabase_client

from .models import EnvironmentalSnapshot

logger = logging.getLogger(__name__)


class SupabaseEnvironmentStore:
    """Persist :class:`EnvironmentalSnapshot` rows to the Supabase table.

    Implements :class:`~backend.services.environment.interfaces.IEnvironmentStore`.

    Parameters
    ----------
    client:
        Supabase client.  Defaults to the shared global singleton so normal
        production code needs no extra configuration.  Tests can inject a
        mock client directly.
    """

    def __init__(self, client: Optional[Client] = None) -> None:
        self._client = client or get_supabase_client()

    def save(self, user_id: str, snapshot: EnvironmentalSnapshot) -> None:
        """Insert *snapshot* into ``environmental_data``.

        Failures are caught, logged, and silenced so the RAG pipeline is
        never interrupted by a DB write problem.

        Parameters
        ----------
        user_id:
            UUID of the user who triggered the environment fetch.
        snapshot:
            Populated :class:`EnvironmentalSnapshot` to persist.
        """
        row = {
            "user_id":              user_id,
            "location_city":        snapshot.location_city,
            "latitude":             snapshot.latitude,
            "longitude":            snapshot.longitude,
            "temperature_celsius":  snapshot.temperature_celsius,
            "humidity_percent":     snapshot.humidity_percent,
            "aqi_level":            snapshot.aqi_level,
            "weather_condition":    snapshot.weather_condition,
            "weather_code":         snapshot.weather_code,
            "recorded_at":          snapshot.fetched_at.isoformat(),
        }
        try:
            self._client.table("environmental_data").insert(row).execute()
            logger.debug(
                "Saved environmental snapshot for user_id=%s, city='%s'.",
                user_id, snapshot.location_city,
            )
        except Exception as exc:  # noqa: BLE001
            # Non-fatal: a DB write failure should not break the AI response.
            logger.warning(
                "Failed to save environmental snapshot for user_id=%s, city='%s': %s",
                user_id, snapshot.location_city, exc,
            )


class NullEnvironmentStore:
    """No-op store for unit tests and offline environments.

    Implements :class:`~backend.services.environment.interfaces.IEnvironmentStore`.

    ``save()`` does nothing and produces no side effects.  Swap this in
    during testing so tests do not require a live Supabase connection::

        service = EnvironmentService(
            weather_client=...,
            aqi_client=...,
            store=NullEnvironmentStore(),   # ← test-safe, no DB writes
        )
    """

    def save(self, user_id: str, snapshot: EnvironmentalSnapshot) -> None:  # noqa: ARG002
        """Accept *snapshot* and discard it silently."""
        logger.debug(
            "NullEnvironmentStore: discarding snapshot for user_id=%s, city='%s'.",
            user_id, snapshot.location_city,
        )
