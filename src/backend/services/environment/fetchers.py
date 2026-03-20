"""Concrete Open-Meteo implementations of the environmental data interfaces.

Three classes, one per API endpoint — each has a single responsibility and
implements exactly one protocol:

``OpenMeteoWeatherFetcher`` → :class:`~backend.services.environment.interfaces.IWeatherClient`
``OpenMeteoAQIFetcher``  → :class:`~backend.services.environment.interfaces.IAirQualityClient`

All three are **stateless** (no instance variables beyond optional timeout
configuration) so they can be safely shared across requests as singletons.

Open-Meteo API notes
--------------------
* **Free, no API key required** for all three endpoints used here.
* Rate limits are generous for typical app workloads (~10 000 req/day).
* All responses are JSON with a consistent ``{"current": {...}}`` shape for
  forecast and air-quality endpoints.

References
----------
* Forecast:  https://open-meteo.com/en/docs
* Air quality: https://open-meteo.com/en/docs/air-quality-api
* WMO codes:  https://open-meteo.com/en/docs (scroll to "WMO Weather interpretation codes")
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from .models import AirQualitySnapshot, WeatherSnapshot

logger = logging.getLogger(__name__)

# ── API base URLs ─────────────────────────────────────────────────────────────

_FORECAST_URL  = "https://api.open-meteo.com/v1/forecast"
_AQI_URL       = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Default request timeout in seconds.  Keeps the RAG pipeline responsive even
# if an Open-Meteo data centre is slow.
_DEFAULT_TIMEOUT: float = 8.0

# ── WMO weather code → human-readable label ───────────────────────────────────
# Source: https://open-meteo.com/en/docs (WMO Weather interpretation codes table)
# Only a representative subset is needed; unknown codes fall back to "Unknown".

_WMO_CODES: dict[int, str] = {
    0:  "Clear sky",
    1:  "Mainly clear",
    2:  "Partly cloudy",
    3:  "Overcast",
    45: "Fog",
    48: "Icy fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def _wmo_to_label(code: Optional[int]) -> Optional[str]:
    """Return the human-readable label for a WMO weather code.

    Parameters
    ----------
    code:
        Integer WMO weather interpretation code, or ``None``.

    Returns
    -------
    str or None
        A short descriptive string (e.g. ``"Partly cloudy"``), or ``None``
        when *code* is ``None``.  Unknown codes produce ``"Unknown (code=<n>)"``.
    """
    if code is None:
        return None
    return _WMO_CODES.get(code, f"Unknown (code={code})")


# ── Weather fetcher ───────────────────────────────────────────────────────────

class OpenMeteoWeatherFetcher:
    """Fetch current weather from the Open-Meteo Forecast API.

    Implements :class:`~backend.services.environment.interfaces.IWeatherClient`.

    The three ``current`` variables used here:

    * ``temperature_2m``         — air temperature 2 m above ground (°C)
    * ``relative_humidity_2m``   — relative humidity 2 m above ground (%)
    * ``weather_code``           — WMO weather interpretation code

    Parameters
    ----------
    timeout:
        HTTP request timeout in seconds.
    """

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout

    def fetch_weather(self, latitude: float, longitude: float) -> WeatherSnapshot:
        """Return current weather at the given coordinates.

        Parameters
        ----------
        latitude:
            Decimal degrees north.
        longitude:
            Decimal degrees east.

        Returns
        -------
        WeatherSnapshot

        Raises
        ------
        RuntimeError
            If the HTTP call fails.
        """
        logger.debug("Fetching weather for lat=%.4f, lon=%.4f", latitude, longitude)
        try:
            response = httpx.get(
                _FORECAST_URL,
                params={
                    "latitude":  latitude,
                    "longitude": longitude,
                    "current":   "temperature_2m,relative_humidity_2m,weather_code",
                },
                timeout=self._timeout,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Forecast API request failed for lat={latitude}, lon={longitude}: {exc}"
            ) from exc

        current = data.get("current") or {}
        code = current.get("weather_code")

        snapshot = WeatherSnapshot(
            temperature_celsius=current.get("temperature_2m"),
            humidity_percent=current.get("relative_humidity_2m"),
            weather_code=code,
            weather_condition=_wmo_to_label(code),
        )
        logger.debug(
            "Weather snapshot: temp=%.1f°C, humidity=%.0f%%, condition=%s",
            snapshot.temperature_celsius or 0,
            snapshot.humidity_percent or 0,
            snapshot.weather_condition,
        )
        return snapshot


# ── AQI fetcher ───────────────────────────────────────────────────────────────

class OpenMeteoAQIFetcher:
    """Fetch current US AQI from the Open-Meteo Air Quality API.

    Implements :class:`~backend.services.environment.interfaces.IAirQualityClient`.

    The API returns the European Air Quality Index alongside the US AQI;
    we specifically request and return only the US AQI (``us_aqi``) since
    it is the most internationally recognised scale.

    Parameters
    ----------
    timeout:
        HTTP request timeout in seconds.
    """

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout

    def fetch_aqi(self, latitude: float, longitude: float) -> AirQualitySnapshot:
        """Return current US AQI at the given coordinates.

        Parameters
        ----------
        latitude:
            Decimal degrees north.
        longitude:
            Decimal degrees east.

        Returns
        -------
        AirQualitySnapshot

        Raises
        ------
        RuntimeError
            If the HTTP call fails.
        """
        logger.debug("Fetching AQI for lat=%.4f, lon=%.4f", latitude, longitude)
        try:
            response = httpx.get(
                _AQI_URL,
                params={
                    "latitude":  latitude,
                    "longitude": longitude,
                    "current":   "us_aqi",
                },
                timeout=self._timeout,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Air Quality API request failed for lat={latitude}, lon={longitude}: {exc}"
            ) from exc

        current = data.get("current") or {}
        snapshot = AirQualitySnapshot(us_aqi=current.get("us_aqi"))
        logger.debug("AQI snapshot: us_aqi=%s", snapshot.us_aqi)
        return snapshot
