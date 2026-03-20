"""Orchestrating service for the environmental data pipeline.

``EnvironmentService`` composes the Open-Meteo weather/AQI clients and the DB
store into a single coordinate-first call.  It is the only public entry point
that callers (e.g. ``routes/rag.py``) need to import.

Typical usage (production)
--------------------------
::

    from backend.services.environment import get_environment_service

    _env = get_environment_service()          # singleton, created once

    snapshot = _env.get_snapshot_for_coordinates(
        user_id="<uuid>",
        latitude=17.4065,
        longitude=78.4772,
        location_city="Hyderabad",
    )
    env_dict = snapshot.to_context_dict()      # pass to build_context()

Typical usage (testing)
-----------------------
::

    from backend.services.environment.service import EnvironmentService
    from backend.services.environment.store import NullEnvironmentStore

    service = EnvironmentService(
        weather_client=MyMockWeather(),
        aqi_client=MyMockAQI(),
        store=NullEnvironmentStore(),
    )
"""

from __future__ import annotations

import logging
from typing import Optional

from .fetchers import OpenMeteoAQIFetcher, OpenMeteoWeatherFetcher
from .interfaces import IAirQualityClient, IWeatherClient, IEnvironmentStore
from .models import EnvironmentalSnapshot
from .store import SupabaseEnvironmentStore

logger = logging.getLogger(__name__)


class EnvironmentService:
    """Orchestrate weather/AQI fetching and DB caching with coordinates.

    Parameters
    ----------
    weather_client:
        Any object satisfying :class:`~backend.services.environment.interfaces.IWeatherClient`.
    aqi_client:
        Any object satisfying :class:`~backend.services.environment.interfaces.IAirQualityClient`.
    store:
        Any object satisfying :class:`~backend.services.environment.interfaces.IEnvironmentStore`.
        Defaults to :class:`~backend.services.environment.store.SupabaseEnvironmentStore`.
    """

    def __init__(
        self,
        weather_client: IWeatherClient,
        aqi_client: IAirQualityClient,
        store: IEnvironmentStore,
    ) -> None:
        self._weather  = weather_client
        self._aqi      = aqi_client
        self._store    = store

    def get_snapshot_for_coordinates(
        self,
        *,
        user_id: str,
        latitude: float,
        longitude: float,
        location_city: Optional[str] = None,
    ) -> EnvironmentalSnapshot:
        """Fetch and cache an environmental snapshot using caller-supplied coordinates.

        This is the preferred path for mobile clients that already have GPS
        coordinates.  It bypasses geocoding entirely, reducing latency and
        eliminating city-name ambiguity.

        Parameters
        ----------
        user_id:
            UUID of the requesting user.
        latitude:
            GPS latitude in decimal degrees.
        longitude:
            GPS longitude in decimal degrees.
        location_city:
            Optional human-readable city label from the client.  Used only for
            display/audit in DB rows; retrieval calls use exact coordinates.
        """
        label = (location_city or "Unknown").strip() or "Unknown"
        logger.info(
            "Fetching environmental snapshot for user_id=%s at lat=%.5f lon=%.5f",
            user_id,
            latitude,
            longitude,
        )
        return self._build_snapshot_from_coordinates(
            user_id=user_id,
            location_city=label,
            latitude=latitude,
            longitude=longitude,
        )

    def _build_snapshot_from_coordinates(
        self,
        *,
        user_id: str,
        location_city: str,
        latitude: float,
        longitude: float,
    ) -> EnvironmentalSnapshot:
        """Create, persist, and return an environmental snapshot for coordinates.

        Private helper for coordinate-first environmental snapshots.
        """
        # ── Step B: Weather (best-effort) ─────────────────────────────────────
        temperature_celsius: Optional[float] = None
        humidity_percent:    Optional[float] = None
        weather_condition:   Optional[str]   = None
        weather_code:        Optional[int]   = None
        try:
            weather = self._weather.fetch_weather(latitude, longitude)
            temperature_celsius = weather.temperature_celsius
            humidity_percent    = weather.humidity_percent
            weather_condition   = weather.weather_condition
            weather_code        = weather.weather_code
        except RuntimeError as exc:
            logger.warning(
                "Weather fetch failed for lat=%.5f lon=%.5f (non-fatal): %s",
                latitude,
                longitude,
                exc,
            )

        # ── Step C: AQI (best-effort) ──────────────────────────────────────────
        aqi_level: Optional[int] = None
        try:
            aqi = self._aqi.fetch_aqi(latitude, longitude)
            aqi_level = aqi.us_aqi
        except RuntimeError as exc:
            logger.warning(
                "AQI fetch failed for lat=%.5f lon=%.5f (non-fatal): %s",
                latitude,
                longitude,
                exc,
            )

        # ── Step D: Merge ─────────────────────────────────────────────────────
        snapshot = EnvironmentalSnapshot(
            location_city=location_city,
            latitude=latitude,
            longitude=longitude,
            temperature_celsius=temperature_celsius,
            humidity_percent=humidity_percent,
            aqi_level=aqi_level,
            weather_condition=weather_condition,
            weather_code=weather_code,
        )

        # ── Step E: Persist (best-effort; handled inside store.save) ──────────
        self._store.save(user_id=user_id, snapshot=snapshot)

        logger.info(
            "Environmental snapshot ready: city='%s', lat=%.5f lon=%.5f, "
            "temp=%.1f°C, aqi=%s, condition=%s",
            location_city,
            latitude,
            longitude,
            temperature_celsius or 0,
            aqi_level,
            weather_condition,
        )
        return snapshot


# ── Factory ───────────────────────────────────────────────────────────────────

def get_environment_service() -> EnvironmentService:
    """Create an :class:`EnvironmentService` wired with production defaults.

    Returns a new instance on each call; callers that want a singleton should
    store the result at module level::

        _env_service = get_environment_service()

    Returns
    -------
    EnvironmentService
        Ready-to-use service backed by Open-Meteo APIs and Supabase storage.
    """
    return EnvironmentService(
        weather_client=OpenMeteoWeatherFetcher(),
        aqi_client=OpenMeteoAQIFetcher(),
        store=SupabaseEnvironmentStore(),
    )
