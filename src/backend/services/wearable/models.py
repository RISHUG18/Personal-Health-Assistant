"""Pydantic data-transfer objects for the wearable vitals pipeline.

Models represent stages of the ingestion and aggregation flow:

1. ``VitalReading``        — single metric reading from a device
2. ``VitalsBatch``         — batch of readings for ingestion
3. ``MetricSummary``       — aggregated stats for one metric type
4. ``VitalsSummary``       — complete 7-day summary for context builder

Design
------
* Models are **pure data containers** — no I/O, no database calls.
* ``VitalsSummary.to_context_dict()`` produces the exact dict shape expected
  by the context builder's ``WearableData`` model.
* All timestamps use timezone-aware datetimes for consistency.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class VitalReading(BaseModel):
    """A single vital metric reading from a wearable device.

    Used for batch ingestion via POST /ingest/vitals.
    """
    recorded_at: datetime = Field(
        ...,
        description="Timestamp when the metric was measured by the device"
    )
    metric_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Type of metric (e.g., heart_rate, steps, sleep_minutes)"
    )
    value: float = Field(
        ...,
        description="Numeric value of the metric"
    )
    unit: Optional[str] = Field(
        None,
        max_length=20,
        description="Unit of measurement (e.g., bpm, steps, minutes)"
    )
    device_id: Optional[str] = Field(
        None,
        max_length=100,
        description="Optional device identifier"
    )

    @field_validator("metric_type")
    @classmethod
    def normalize_metric_type(cls, v: str) -> str:
        """Normalize metric type to lowercase with underscores."""
        return v.strip().lower().replace(" ", "_").replace("-", "_")


class VitalsBatch(BaseModel):
    """Batch of vital readings for ingestion.

    Accepted by POST /ingest/vitals endpoint.
    """
    user_id: str = Field(..., description="UUID of the user")
    readings: List[VitalReading] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of vital readings to ingest (max 1000 per batch)"
    )


class MetricSummary(BaseModel):
    """Aggregated statistics for a single metric type over a time period.

    Returned by the get_vitals_summary RPC function.
    """
    metric_type: str
    avg_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    latest_value: Optional[float] = None
    sample_count: int = 0
    unit: Optional[str] = None


class VitalsSummary(BaseModel):
    """Complete vitals summary for the context builder.

    Aggregates multiple metric types over the last N days.
    """
    user_id: str
    period_days: int = 7
    metrics: List[MetricSummary] = Field(default_factory=list)
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_context_dict(self) -> Dict[str, Any]:
        """Convert summary to a dict compatible with the context builder.

        Maps aggregated metrics to the WearableData schema expected by
        build_context(). Uses the latest values for point-in-time fields
        and averages for ranges.

        Returns
        -------
        dict
            Shape compatible with WearableData Pydantic model.
        """
        # Build lookup for quick metric access
        by_type: Dict[str, MetricSummary] = {m.metric_type: m for m in self.metrics}

        def get_latest(key: str) -> Optional[float]:
            return by_type.get(key, MetricSummary(metric_type=key)).latest_value

        def get_avg(key: str) -> Optional[float]:
            return by_type.get(key, MetricSummary(metric_type=key)).avg_value

        # Map to context builder schema
        return {
            "device_synced_at": self.generated_at.isoformat(),
            "activity_summary": {
                "steps_today": int(get_latest("steps")) if get_latest("steps") else None,
                "calories_burned": int(get_latest("calories_burned")) if get_latest("calories_burned") else None,
                "active_minutes": int(get_latest("active_minutes")) if get_latest("active_minutes") else None,
            },
            "sleep_metrics": {
                "total_sleep_hours": round(get_avg("sleep_minutes") / 60, 2) if get_avg("sleep_minutes") else None,
                "sleep_score": int(get_latest("sleep_score")) if get_latest("sleep_score") else None,
                "deep_sleep_minutes": int(get_avg("deep_sleep_minutes")) if get_avg("deep_sleep_minutes") else None,
            },
            "heart_health": {
                "resting_heart_rate": int(get_avg("resting_heart_rate")) if get_avg("resting_heart_rate") else None,
                "hrv_score": int(get_avg("hrv_ms")) if get_avg("hrv_ms") else None,
            },
            # Additional raw metrics for the 7-day summary
            "vitals_7day_summary": {
                m.metric_type: {
                    "avg": m.avg_value,
                    "min": m.min_value,
                    "max": m.max_value,
                    "latest": m.latest_value,
                    "samples": m.sample_count,
                    "unit": m.unit,
                }
                for m in self.metrics
            },
        }


class IngestionResult(BaseModel):
    """Result of a batch ingestion operation."""
    inserted: int = 0
    skipped: int = 0
    errors: List[str] = Field(default_factory=list)
