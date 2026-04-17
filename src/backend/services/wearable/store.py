"""Supabase-backed implementation of IVitalsStore and IVitalsAggregator.

Handles both ingestion (batch inserts) and aggregation (RPC calls) for
the wearable_vitals table defined in migration 006.

Design
------
* **Single Responsibility**: this module handles DB operations only.
* **Dependency Inversion**: callers depend on IVitalsStore/IVitalsAggregator;
  this concrete class is injected, never imported directly by callers.
* Batch inserts are best-effort: duplicates are skipped, not errored.
* Aggregation uses the get_vitals_summary RPC function for efficiency.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import List, Optional

from supabase import Client

from backend.config.supabase_client import get_supabase_client

from .models import IngestionResult, MetricSummary, VitalReading

logger = logging.getLogger(__name__)


class SupabaseVitalsStore:
    """Supabase implementation of IVitalsStore and IVitalsAggregator.

    Parameters
    ----------
    client:
        Supabase client. Defaults to the shared global singleton.
        Tests can inject a mock client directly.
    """

    def __init__(self, client: Optional[Client] = None) -> None:
        self._client = client or get_supabase_client()

    def insert_batch(
        self,
        user_id: str,
        readings: List[VitalReading],
    ) -> IngestionResult:
        """Insert a batch of vital readings, always overwriting on conflict.

        Uses upsert with ``ON CONFLICT DO UPDATE`` (``ignore_duplicates=False``)
        so that every sync writes the latest value for each
        ``(user_id, recorded_at, metric_type)`` key.

        This is the correct strategy for all metric types:

        * **Daily-aggregated metrics** (steps, calories, heart_rate): the Android
          pre-aggregates to one row per calendar day using a deterministic midnight
          timestamp.  A later sync of the same day has a higher cumulative total
          (more steps walked), so the overwrite always improves the stored value.
        * **Raw-event metrics** (sleep, HRV, SpO2): each reading carries a real
          device-event timestamp unique per occurrence.  No two events share the
          same ``(user_id, recorded_at, metric_type)`` key, so no conflict ever
          occurs and the upsert behaves identically to a plain insert.

        Parameters
        ----------
        user_id:
            UUID of the user.
        readings:
            List of VitalReading objects to insert.

        Returns
        -------
        IngestionResult
            Summary with counts of inserted, skipped, and errored readings.
        """
        if not readings:
            return IngestionResult(inserted=0, skipped=0, errors=[])

        result = IngestionResult()

        rows = [
            {
                "user_id": user_id,
                "recorded_at": reading.recorded_at.isoformat(),
                "metric_type": reading.metric_type,
                "value": reading.value,
                "unit": reading.unit,
                "device_id": reading.device_id,
            }
            for reading in readings
        ]

        try:
            response = (
                self._client.table("wearable_vitals")
                .upsert(
                    rows,
                    on_conflict="user_id,recorded_at,metric_type",
                    ignore_duplicates=False,  # always UPDATE value on conflict
                )
                .execute()
            )

            result.inserted = len(response.data) if response.data else 0
            result.skipped = 0  # with overwrite, nothing is truly skipped

            logger.info(
                "Vitals batch insert: user_id=%s, total=%d, upserted=%d",
                user_id,
                len(readings),
                result.inserted,
            )

        except Exception as exc:
            logger.error(
                "Vitals batch insert failed: user_id=%s, error=%s",
                user_id,
                exc,
            )
            result.errors.append(str(exc))
            result.skipped = len(readings)

        return result

    def get_readings(
        self,
        user_id: str,
        metric_type: Optional[str] = None,
        days: int = 7,
        limit: int = 1000,
    ) -> List[dict]:
        """Retrieve raw readings for a user within a time window.

        Parameters
        ----------
        user_id:
            UUID of the user.
        metric_type:
            Optional filter for specific metric type.
        days:
            Number of days to look back.
        limit:
            Maximum readings to return.

        Returns
        -------
        List[dict]
            Raw reading rows ordered by recorded_at DESC.
        """
        try:
            safe_days = max(int(days), 1)
            cutoff = (datetime.now(timezone.utc) - timedelta(days=safe_days)).isoformat()

            query = (
                self._client.table("wearable_vitals")
                .select("*")
                .eq("user_id", user_id)
                .gte("recorded_at", cutoff)
                .order("recorded_at", desc=True)
                .limit(limit)
            )

            if metric_type:
                query = query.eq("metric_type", metric_type)

            response = query.execute()
            return response.data or []

        except Exception as exc:
            logger.warning(
                "get_readings failed: user_id=%s, metric=%s, error=%s",
                user_id,
                metric_type,
                exc,
            )
            return []

    def get_summary(
        self,
        user_id: str,
        days: int = 7,
        timezone: str = "UTC",
    ) -> List[MetricSummary]:
        """Call the get_vitals_summary RPC function for aggregated stats.

        Parameters
        ----------
        user_id:
            UUID of the user.
        days:
            Number of days to aggregate.
        timezone:
            IANA timezone string for local-day bucketing of trend points
            (e.g. ``'Asia/Kolkata'``).  Defaults to ``'UTC'`` for backwards
            compatibility.  Pass the user's device timezone so the 7-day
            trend graph aligns with local calendar days, not UTC dates.

        Returns
        -------
        List[MetricSummary]
            Aggregated stats for each metric type.
        """
        try:
            response = self._client.rpc(
                "get_vitals_summary",
                {"p_user_id": user_id, "p_days": days, "p_timezone": timezone}
            ).execute()

            summaries = []
            for row in response.data or []:
                raw_trend_points = row.get("trend_points")
                trend_points = None
                if raw_trend_points is not None:
                    trend_points = [
                        float(point)
                        for point in raw_trend_points
                        if point is not None
                    ]

                summaries.append(
                    MetricSummary(
                        metric_type=row.get("metric_type", ""),
                        avg_value=float(row["avg_value"]) if row.get("avg_value") is not None else None,
                        min_value=float(row["min_value"]) if row.get("min_value") is not None else None,
                        max_value=float(row["max_value"]) if row.get("max_value") is not None else None,
                        latest_value=float(row["latest_value"]) if row.get("latest_value") is not None else None,
                        trend_points=trend_points,
                        sample_count=int(row.get("sample_count", 0)),
                        unit=row.get("unit"),
                    )
                )

            logger.debug(
                "get_summary: user_id=%s, days=%d, timezone=%s, metrics=%d",
                user_id,
                days,
                timezone,
                len(summaries),
            )
            return summaries

        except Exception as exc:
            logger.warning(
                "get_summary RPC failed: user_id=%s, error=%s",
                user_id,
                exc,
            )
            return []


class NullVitalsStore:
    """No-op implementation for testing environments.

    All operations succeed but do nothing.
    """

    def insert_batch(
        self,
        user_id: str,
        readings: List[VitalReading],
    ) -> IngestionResult:
        """Pretend to insert readings."""
        return IngestionResult(inserted=len(readings), skipped=0, errors=[])

    def get_readings(
        self,
        user_id: str,
        metric_type: Optional[str] = None,
        days: int = 7,
        limit: int = 1000,
    ) -> List[dict]:
        """Return empty list."""
        return []

    def get_summary(
        self,
        user_id: str,
        days: int = 7,
    ) -> List[MetricSummary]:
        """Return empty summary."""
        return []
