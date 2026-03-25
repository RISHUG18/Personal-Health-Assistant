"""HTTP routes for fetching real-time environmental data (AQI, Weather)."""

from fastapi import APIRouter, HTTPException, Query, status

from backend.services.environment import get_environment_service
from backend.services.environment.models import EnvironmentalSnapshot

router = APIRouter(prefix="/api/v1/environment", tags=["environment"])

# Module-level singleton to avoid repeated instantiation.
_env_service = get_environment_service()


@router.get("", status_code=status.HTTP_200_OK)
async def get_environment_data(
    user_id: str = Query(..., description="UUID of the user making the request"),
    latitude: float = Query(..., description="GPS latitude coordinate", ge=-90, le=90),
    longitude: float = Query(..., description="GPS longitude coordinate", ge=-180, le=180),
    city: str | None = Query(None, description="Optional city name for display"),
) -> dict:
    """Fetch real-time AQI and weather data for the given GPS coordinates.

    This endpoint uses the Open-Meteo API to retrieve:
    - Current temperature (Celsius)
    - Humidity percentage
    - Weather condition (derived from WMO code)
    - US Air Quality Index (AQI)

    The response is cached in the database and returned to the client.

    Parameters
    ----------
    user_id
        UUID of the user requesting environmental data.
    latitude
        GPS latitude (-90 to 90).
    longitude
        GPS longitude (-180 to 180).
    city
        Optional city name for display purposes.

    Returns
    -------
    dict
        Environmental snapshot with keys:
        - location_city
        - latitude
        - longitude
        - temperature_celsius
        - humidity_percent
        - aqi_level
        - weather_condition
        - fetched_at (ISO timestamp)
    """
    try:
        snapshot: EnvironmentalSnapshot = _env_service.get_snapshot_for_coordinates(
            user_id=user_id,
            latitude=latitude,
            longitude=longitude,
            location_city=city,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch environmental data: {exc}",
        ) from exc

    # Return full snapshot for Android client (includes lat/lon for display).
    return {
        "location_city": snapshot.location_city,
        "latitude": snapshot.latitude,
        "longitude": snapshot.longitude,
        "temperature_celsius": snapshot.temperature_celsius,
        "humidity_percent": snapshot.humidity_percent,
        "aqi_level": snapshot.aqi_level,
        "weather_condition": snapshot.weather_condition,
        "fetched_at": snapshot.fetched_at.isoformat(),
    }
