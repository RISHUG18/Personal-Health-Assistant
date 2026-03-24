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
        """Insert a batch of vital readings, handling duplicates gracefully.

        Uses upsert with ON CONFLICT DO NOTHING to skip duplicates
        (same user_id, recorded_at, metric_type).

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
        rows = []

        for reading in readings:
            rows.append({
                "user_id": user_id,
                "recorded_at": reading.recorded_at.isoformat(),
                "metric_type": reading.metric_type,
                "value": reading.value,
                "unit": reading.unit,
                "device_id": reading.device_id,
            })

        try:
            # Use upsert with ignoreDuplicates to skip conflicts
            response = (
                self._client.table("wearable_vitals")
                .upsert(rows, on_conflict="user_id,recorded_at,metric_type", ignore_duplicates=True)
                .execute()
            )

            # Count actual inserts vs skips
            inserted_count = len(response.data) if response.data else 0
            result.inserted = inserted_count
            result.skipped = len(readings) - inserted_count

            logger.info(
                "Vitals batch insert: user_id=%s, total=%d, inserted=%d, skipped=%d",
                user_id,
                len(readings),
                result.inserted,
                result.skipped,
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
            query = (
                self._client.table("wearable_vitals")
                .select("*")
                .eq("user_id", user_id)
                .gte("recorded_at", f"now() - interval '{days} days'")
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
    ) -> List[MetricSummary]:
        """Call the get_vitals_summary RPC function for aggregated stats.

        Parameters
        ----------
        user_id:
            UUID of the user.
        days:
            Number of days to aggregate.

        Returns
        -------
        List[MetricSummary]
            Aggregated stats for each metric type.
        """
        try:
            response = self._client.rpc(
                "get_vitals_summary",
                {"p_user_id": user_id, "p_days": days}
            ).execute()

            summaries = []
            for row in response.data or []:
                summaries.append(
                    MetricSummary(
                        metric_type=row.get("metric_type", ""),
                        avg_value=float(row["avg_value"]) if row.get("avg_value") is not None else None,
                        min_value=float(row["min_value"]) if row.get("min_value") is not None else None,
                        max_value=float(row["max_value"]) if row.get("max_value") is not None else None,
                        latest_value=float(row["latest_value"]) if row.get("latest_value") is not None else None,
                        sample_count=int(row.get("sample_count", 0)),
                        unit=row.get("unit"),
                    )
                )

            logger.debug(
                "get_summary: user_id=%s, days=%d, metrics=%d",
                user_id,
                days,
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
