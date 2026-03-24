"""Environmental data helper for the Vitalis rules engine.

This module provides an adapter to safely fetch environmental data
from the `environmental_data` table for the deterministic rules engine.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from supabase import Client

_log = logging.getLogger(__name__)


def get_environmental_data(
    client: Client,
    user_id: str,
    location: Optional[str] = None,
    date: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieve the most recent environmental snapshot for *user_id*.

    Returns a dict with the exact fields requested for the Person 1 task:
    - aqi
    - temperature
    - humidity
    - location
    - date

    If data is missing or the query fails, returns None.

    Args:
        client:   A Supabase ``Client`` instance.
        user_id:  UUID string identifying the user.
        location: Optional fallback filter for city.
        date:     Optional exact timestamp/date filter (currently ignored in favor of most recent).

    Returns:
        A dict of environmental evidence or None.
    """
    if not user_id:
        return None

    try:
        query = (
            client.table("environmental_data")
            .select(
                "location_city, temperature_celsius, humidity_percent, aqi_level, recorded_at"
            )
            .eq("user_id", user_id)
            .order("recorded_at", desc=True)
            .limit(1)
        )
        if location:
            query = query.eq("location_city", location)

        response = query.execute()
        rows = response.data or []

        if not rows:
            return None

        row = rows[0]
        
        # We handle potential null values inside the fields gracefully
        _log.info("Fetched environmental data for user_id=%s via rules engine adapter", user_id)
        return {
            "aqi": row.get("aqi_level"),
            "temperature": row.get("temperature_celsius"),
            "humidity": row.get("humidity_percent"),
            "location": row.get("location_city"),
            "date": row.get("recorded_at"),
        }

    except Exception as exc:  # noqa: BLE001
        _log.warning(
            "get_environmental_data failed for user_id=%s: %s", user_id, exc
        )
        return None
