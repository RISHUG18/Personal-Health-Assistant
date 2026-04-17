"""Abstract protocol interfaces for the wearable vitals pipeline.

By depending on these abstractions rather than concrete implementations,
callers (``WearableService``) honour the Dependency Inversion Principle —
concrete stores and aggregators can be swapped, mocked, or extended without
touching the orchestrating service.

Interface summary
-----------------
``IVitalsStore``
    Persists and retrieves wearable vital readings from a data store.
``IVitalsAggregator``
    Computes aggregated summaries (avg, min, max) over time periods.
"""

from __future__ import annotations

from typing import List, Protocol, runtime_checkable

from .models import IngestionResult, MetricSummary, VitalReading


@runtime_checkable
class IVitalsStore(Protocol):
    """Store and retrieve wearable vital readings.

    Implementors
    ------------
    * :class:`~backend.services.wearable.store.SupabaseVitalsStore`
    * :class:`~backend.services.wearable.store.NullVitalsStore` (testing)
    """

    def insert_batch(
        self,
        user_id: str,
        readings: List[VitalReading],
    ) -> IngestionResult:
        """Insert a batch of vital readings for a user.

        Parameters
        ----------
        user_id:
            UUID of the user whose vitals are being recorded.
        readings:
            List of VitalReading objects to persist.

        Returns
        -------
        IngestionResult
            Summary of inserted, skipped (duplicates), and errored readings.
        """
        ...

    def get_readings(
        self,
        user_id: str,
        metric_type: str | None = None,
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
            Number of days to look back (default: 7).
        limit:
            Maximum number of readings to return.

        Returns
        -------
        List[dict]
            Raw reading rows from the database.
        """
        ...


@runtime_checkable
class IVitalsAggregator(Protocol):
    """Compute aggregated vitals summaries over time periods.

    Implementors
    ------------
    * :class:`~backend.services.wearable.store.SupabaseVitalsStore`
      (implements both IVitalsStore and IVitalsAggregator)
    """

    def get_summary(
        self,
        user_id: str,
        days: int = 7,
        timezone: str = "UTC",
    ) -> List[MetricSummary]:
        """Compute aggregated summary for all metric types.

        Parameters
        ----------
        user_id:
            UUID of the user.
        days:
            Number of days to aggregate (default: 7).
        timezone:
            IANA timezone string for local-day trend bucketing
            (e.g. ``'Asia/Kolkata'``). Defaults to ``'UTC'``.

        Returns
        -------
        List[MetricSummary]
            Aggregated stats for each metric type found.
        """
        ...
