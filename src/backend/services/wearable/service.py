"""Wearable vitals orchestration service.

The ``WearableService`` class coordinates between:

* **Ingestion**: Accepting batch readings from devices/apps
* **Storage**: Persisting to the wearable_vitals table
* **Aggregation**: Computing 7-day summaries for the context builder

Design
------
* **Single Responsibility**: orchestrates flow, delegates I/O to store.
* **Dependency Inversion**: depends on IVitalsStore protocol, not concrete class.
* **Factory function**: ``get_wearable_service()`` wires production dependencies.

Usage
-----
::

    from backend.services.wearable import get_wearable_service, VitalsBatch

    service = get_wearable_service()

    # Ingest batch
    result = service.ingest_batch(batch)

    # Get 7-day summary for context builder
    summary = service.get_vitals_summary(user_id="<uuid>")
    context_dict = summary.to_context_dict()
"""

from __future__ import annotations

import logging
from typing import List, Optional

from .interfaces import IVitalsAggregator, IVitalsStore
from .models import IngestionResult, MetricSummary, VitalReading, VitalsSummary
from .store import SupabaseVitalsStore

logger = logging.getLogger(__name__)

# Module-level singleton for the default service instance
_default_service: Optional["WearableService"] = None


class WearableService:
    """Orchestrates wearable vitals ingestion and aggregation.

    Parameters
    ----------
    store:
        Implementation of IVitalsStore for persistence.
    aggregator:
        Implementation of IVitalsAggregator for summaries.
        Often the same object as store (SupabaseVitalsStore implements both).
    """

    def __init__(
        self,
        store: IVitalsStore,
        aggregator: IVitalsAggregator,
    ) -> None:
        self._store = store
        self._aggregator = aggregator

    def ingest_batch(
        self,
        user_id: str,
        readings: List[VitalReading],
    ) -> IngestionResult:
        """Ingest a batch of vital readings for a user.

        Parameters
        ----------
        user_id:
            UUID of the user.
        readings:
            List of VitalReading objects to persist.

        Returns
        -------
        IngestionResult
            Summary of the ingestion operation.
        """
        if not user_id:
            return IngestionResult(
                inserted=0,
                skipped=len(readings),
                errors=["user_id is required"],
            )

        if not readings:
            return IngestionResult(inserted=0, skipped=0, errors=[])

        logger.info(
            "Ingesting vitals batch: user_id=%s, readings=%d",
            user_id,
            len(readings),
        )

        return self._store.insert_batch(user_id, readings)

    def get_vitals_summary(
        self,
        user_id: str,
        days: int = 7,
    ) -> VitalsSummary:
        """Get aggregated vitals summary for the context builder.

        Parameters
        ----------
        user_id:
            UUID of the user.
        days:
            Number of days to aggregate (default: 7).

        Returns
        -------
        VitalsSummary
            Complete summary with all metric aggregations.
        """
        if not user_id:
            logger.warning("get_vitals_summary called with empty user_id")
            return VitalsSummary(user_id="", period_days=days, metrics=[])

        metrics: List[MetricSummary] = self._aggregator.get_summary(user_id, days)

        logger.debug(
            "Vitals summary: user_id=%s, days=%d, metric_types=%d",
            user_id,
            days,
            len(metrics),
        )

        return VitalsSummary(
            user_id=user_id,
            period_days=days,
            metrics=metrics,
        )

    def get_raw_readings(
        self,
        user_id: str,
        metric_type: Optional[str] = None,
        days: int = 7,
        limit: int = 1000,
    ) -> List[dict]:
        """Get raw readings (not aggregated) for detailed analysis.

        Parameters
        ----------
        user_id:
            UUID of the user.
        metric_type:
            Optional filter for specific metric.
        days:
            Number of days to look back.
        limit:
            Maximum readings to return.

        Returns
        -------
        List[dict]
            Raw reading rows from the database.
        """
        return self._store.get_readings(user_id, metric_type, days, limit)


def get_wearable_service() -> WearableService:
    """Factory function returning the production WearableService singleton.

    The store is created once and reused across all requests within the
    same process, avoiding repeated Supabase client initialization.

    Returns
    -------
    WearableService
        The shared service instance configured with SupabaseVitalsStore.
    """
    global _default_service

    if _default_service is None:
        store = SupabaseVitalsStore()
        # SupabaseVitalsStore implements both IVitalsStore and IVitalsAggregator
        _default_service = WearableService(store=store, aggregator=store)
        logger.info("WearableService singleton initialized")

    return _default_service
