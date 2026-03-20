"""Abstract protocol interfaces for the environmental data pipeline.

By depending on these abstractions rather than concrete implementations,
callers (``EnvironmentService``) honour the Dependency Inversion Principle —
concrete HTTP clients and DB writers can be swapped out, mocked, or extended
without touching the orchestrating service.

Interface summary
-----------------
``IWeatherClient``
    Fetches current temperature, humidity, and WMO weather code for a
    coordinate pair.
``IAirQualityClient``
    Fetches the current US AQI for a coordinate pair.
``IEnvironmentStore``
    Persists an :class:`~backend.services.environment.models.EnvironmentalSnapshot`
    to a data store (Supabase in production; a no-op stub in tests).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import (
    AirQualitySnapshot,
    EnvironmentalSnapshot,
    WeatherSnapshot,
)


@runtime_checkable
class IWeatherClient(Protocol):
    """Fetch current weather conditions for a lat/lon pair.

    Implementors
    ------------
    * :class:`~backend.services.environment.fetchers.OpenMeteoWeatherFetcher`
    """

    def fetch_weather(self, latitude: float, longitude: float) -> WeatherSnapshot:
        """Return current weather at (*latitude*, *longitude*).

        Parameters
        ----------
        latitude:
            Decimal degrees north.
        longitude:
            Decimal degrees east.

        Returns
        -------
        WeatherSnapshot
            Temperature, humidity, and WMO weather code.

        Raises
        ------
        RuntimeError
            If the forecast API call fails.
        """
        ...


@runtime_checkable
class IAirQualityClient(Protocol):
    """Fetch current US AQI for a lat/lon pair.

    Implementors
    ------------
    * :class:`~backend.services.environment.fetchers.OpenMeteoAQIFetcher`
    """

    def fetch_aqi(self, latitude: float, longitude: float) -> AirQualitySnapshot:
        """Return current air quality at (*latitude*, *longitude*).

        Parameters
        ----------
        latitude:
            Decimal degrees north.
        longitude:
            Decimal degrees east.

        Returns
        -------
        AirQualitySnapshot
            US AQI on the 0–500 scale.

        Raises
        ------
        RuntimeError
            If the air quality API call fails.
        """
        ...


@runtime_checkable
class IEnvironmentStore(Protocol):
    """Persist an :class:`EnvironmentalSnapshot` to a data store.

    Implementors
    ------------
    * :class:`~backend.services.environment.store.SupabaseEnvironmentStore`
    * A no-op :class:`NullEnvironmentStore` for test environments where DB
      writes are undesirable.
    """

    def save(self, user_id: str, snapshot: EnvironmentalSnapshot) -> None:
        """Insert *snapshot* into persistent storage.

        Parameters
        ----------
        user_id:
            UUID of the user who triggered the fetch.
        snapshot:
            Fully populated snapshot to persist.
        """
        ...
