"""HTTP routes for wearable vitals ingestion and retrieval.

POST /ingest/vitals
    Batch ingest vital readings from wearable devices.

GET /vitals/{user_id}/summary
    Get aggregated 7-day vitals summary for the context builder.

GET /vitals/{user_id}/readings
    Get raw readings (not aggregated) for detailed analysis.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.services.wearable import (
    IngestionResult,
    VitalReading,
    VitalsBatch,
    VitalsSummary,
    get_wearable_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["vitals"])

# Module-level singleton — avoids recreating the service on every request
_wearable_service = get_wearable_service()


# ── Request/Response Models ───────────────────────────────────────────────────


class IngestVitalsRequest(BaseModel):
    """Request body for POST /ingest/vitals."""
    user_id: str = Field(..., description="UUID of the user")
    readings: list[VitalReading] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Array of vital readings to ingest (max 1000)"
    )


class IngestVitalsResponse(BaseModel):
    """Response for POST /ingest/vitals."""
    user_id: str
    inserted: int
    skipped: int
    total: int
    errors: list[str] = Field(default_factory=list)


class SummaryResponse(BaseModel):
    """Response for GET /vitals/{user_id}/summary."""
    user_id: str
    period_days: int
    metric_count: int
    summary: dict
    wearable_context: dict  # Ready for context builder


# ── POST /ingest/vitals ───────────────────────────────────────────────────────


@router.post(
    "/ingest/vitals",
    response_model=IngestVitalsResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_vitals(request: IngestVitalsRequest) -> IngestVitalsResponse:
    """Batch ingest vital readings from wearable devices.

    Accepts a JSON array of metric readings and inserts them efficiently
    into the ``wearable_vitals`` table. Duplicates (same user_id, timestamp,
    metric_type) are skipped, not errored.

    **Request body:**
    ```json
    {
      "user_id": "<uuid>",
      "readings": [
        {
          "recorded_at": "2024-01-15T10:30:00Z",
          "metric_type": "heart_rate",
          "value": 72,
          "unit": "bpm",
          "device_id": "fitbit_abc123"
        },
        {
          "recorded_at": "2024-01-15T10:30:00Z",
          "metric_type": "steps",
          "value": 5432,
          "unit": "steps"
        }
      ]
    }
    ```

    **Response:**
    ```json
    {
      "user_id": "<uuid>",
      "inserted": 2,
      "skipped": 0,
      "total": 2,
      "errors": []
    }
    ```

    **Supported metric types:**
    - ``heart_rate`` (bpm)
    - ``steps`` (count)
    - ``sleep_minutes`` (min)
    - ``deep_sleep_minutes`` (min)
    - ``calories_burned`` (kcal)
    - ``active_minutes`` (min)
    - ``spo2`` (%)
    - ``hrv_ms`` (ms)
    - ``resting_heart_rate`` (bpm)
    - ``sleep_score`` (0-100)
    """
    if not request.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id is required",
        )

    if not request.readings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="readings array must not be empty",
        )

    try:
        result: IngestionResult = _wearable_service.ingest_batch(
            user_id=request.user_id,
            readings=request.readings,
        )

        return IngestVitalsResponse(
            user_id=request.user_id,
            inserted=result.inserted,
            skipped=result.skipped,
            total=len(request.readings),
            errors=result.errors,
        )

    except Exception as exc:
        logger.error(
            "Vitals ingestion failed: user_id=%s, error=%s",
            request.user_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vitals ingestion failed: {exc}",
        ) from exc


# ── GET /vitals/{user_id}/summary ─────────────────────────────────────────────


@router.get(
    "/vitals/{user_id}/summary",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
)
async def get_vitals_summary(
    user_id: str,
    days: int = Query(7, ge=1, le=30, description="Number of days to aggregate"),
) -> SummaryResponse:
    """Get aggregated vitals summary for the context builder.

    Computes avg, min, max, and latest values for each metric type
    over the specified number of days (default: 7).

    **Response:**
    ```json
    {
      "user_id": "<uuid>",
      "period_days": 7,
      "metric_count": 5,
      "summary": {
        "heart_rate": {"avg": 72.5, "min": 58, "max": 120, "latest": 68, "samples": 1440},
        "steps": {"avg": 8500, "min": 2000, "max": 15000, "latest": 10234, "samples": 7},
        ...
      },
      "wearable_context": {
        "device_synced_at": "2024-01-15T10:30:00Z",
        "activity_summary": {...},
        "sleep_metrics": {...},
        "heart_health": {...},
        "vitals_7day_summary": {...}
      }
    }
    ```

    The ``wearable_context`` field is ready to pass directly to
    ``build_context(wearable_data=...)``.
    """
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id is required",
        )

    try:
        summary: VitalsSummary = _wearable_service.get_vitals_summary(
            user_id=user_id,
            days=days,
        )

        # Build summary dict from metrics
        summary_dict = {
            m.metric_type: {
                "avg": m.avg_value,
                "min": m.min_value,
                "max": m.max_value,
                "latest": m.latest_value,
                "samples": m.sample_count,
                "unit": m.unit,
            }
            for m in summary.metrics
        }

        return SummaryResponse(
            user_id=user_id,
            period_days=days,
            metric_count=len(summary.metrics),
            summary=summary_dict,
            wearable_context=summary.to_context_dict(),
        )

    except Exception as exc:
        logger.error(
            "get_vitals_summary failed: user_id=%s, error=%s",
            user_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get vitals summary: {exc}",
        ) from exc


# ── GET /vitals/{user_id}/readings ────────────────────────────────────────────


@router.get(
    "/vitals/{user_id}/readings",
    status_code=status.HTTP_200_OK,
)
async def get_vitals_readings(
    user_id: str,
    metric_type: Optional[str] = Query(None, description="Filter by metric type"),
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum readings to return"),
):
    """Get raw vital readings (not aggregated) for detailed analysis.

    Returns individual readings ordered by timestamp (most recent first).
    Use this endpoint when you need detailed time-series data rather than
    aggregated summaries.

    **Response:**
    ```json
    {
      "user_id": "<uuid>",
      "metric_type": "heart_rate",
      "days": 7,
      "count": 100,
      "readings": [
        {
          "id": "...",
          "recorded_at": "2024-01-15T10:30:00Z",
          "metric_type": "heart_rate",
          "value": 72,
          "unit": "bpm",
          "device_id": "fitbit_abc123"
        },
        ...
      ]
    }
    ```
    """
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id is required",
        )

    try:
        readings = _wearable_service.get_raw_readings(
            user_id=user_id,
            metric_type=metric_type,
            days=days,
            limit=limit,
        )

        return {
            "user_id": user_id,
            "metric_type": metric_type,
            "days": days,
            "count": len(readings),
            "readings": readings,
        }

    except Exception as exc:
        logger.error(
            "get_vitals_readings failed: user_id=%s, error=%s",
            user_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get vitals readings: {exc}",
        ) from exc
