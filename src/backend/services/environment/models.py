"""Pydantic data-transfer objects for the environmental data pipeline.

Each model represents one stage of the coordinate-first API chain:

1. ``WeatherSnapshot``    — output of the Forecast API (temperature, humidity, WMO code)
2. ``AirQualitySnapshot`` — output of the Air Quality API (US AQI integer)
3. ``EnvironmentalSnapshot`` — final merged object that is both:
      * inserted into the ``environmental_data`` DB table, and
      * returned as a dict for the RAG context builder.

Design
------
* Models are **pure data containers** — no I/O, no API calls.
* ``EnvironmentalSnapshot.to_context_dict()`` is the only "smart" method; it
  produces the exact dict shape that :class:`~backend.services.context.context_builder.EnvironmentalContext`
  expects, decoupling DB storage shape from LLM prompt shape.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class WeatherSnapshot(BaseModel):
    """Current weather conditions for a coordinate pair.

    Returned by the Open-Meteo Forecast API::

        GET https://api.open-meteo.com/v1/forecast
            ?latitude={lat}&longitude={lon}
            &current=temperature_2m,relative_humidity_2m,weather_code
    """
    temperature_celsius: Optional[float] = None
    humidity_percent: Optional[float] = None
    #: Raw WMO weather interpretation code (0–99).
    weather_code: Optional[int] = None
    #: Human-readable label derived from ``weather_code`` — e.g. "Clear sky".
    weather_condition: Optional[str] = None


class AirQualitySnapshot(BaseModel):
    """Current US AQI for a coordinate pair.

    Returned by the Open-Meteo Air Quality API::

        GET https://air-quality-api.open-meteo.com/v1/air-quality
            ?latitude={lat}&longitude={lon}&current=us_aqi
    """
    #: US AQI on the 0–500 scale; ``None`` when the API returns no value.
    us_aqi: Optional[int] = None


class EnvironmentalSnapshot(BaseModel):
    """Full environmental snapshot: merged output of all three API calls.

    This is the object that is:
    * inserted into the ``environmental_data`` Supabase table, and
    * converted to a context-builder-compatible dict via
      :meth:`to_context_dict`.
    """
    location_city: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    temperature_celsius: Optional[float] = None
    humidity_percent: Optional[float] = None
    aqi_level: Optional[int] = None
    weather_condition: Optional[str] = None
    #: Raw WMO code stored for forward compatibility / debugging.
    weather_code: Optional[int] = None
    #: UTC timestamp of when this snapshot was fetched.
    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_context_dict(self) -> dict:
        """Return a dict compatible with ``EnvironmentalContext`` in the context builder.

        Only the four fields that ``EnvironmentalContext`` cares about are
        included; ``latitude``, ``longitude``, ``weather_code``, and
        ``fetched_at`` are DB-only and are intentionally excluded from the
        LLM prompt to save tokens.

        Returns
        -------
        dict
            Keys: ``location_city``, ``aqi_level``, ``temperature_celsius``,
            ``weather_condition``.
        """
        return {
            "location_city": self.location_city,
            "aqi_level": self.aqi_level,
            "temperature_celsius": self.temperature_celsius,
            "weather_condition": self.weather_condition,
        }
