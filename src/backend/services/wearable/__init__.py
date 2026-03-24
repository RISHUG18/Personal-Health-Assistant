"""Wearable vitals pipeline service package.

Public API
----------
* ``get_wearable_service()`` — factory returning the production singleton
* ``WearableService`` — orchestrating service class
* ``VitalReading``, ``VitalsBatch``, ``VitalsSummary`` — data models
* ``IngestionResult``, ``MetricSummary`` — result types

Usage
-----
Ingestion::

    from backend.services.wearable import get_wearable_service, VitalReading

    service = get_wearable_service()
    result = service.ingest_batch(
        user_id="<uuid>",
        readings=[
            VitalReading(
                recorded_at=datetime.now(timezone.utc),
                metric_type="heart_rate",
                value=72,
                unit="bpm",
            ),
        ],
    )

Aggregation for context builder::

    from backend.services.wearable import get_wearable_service

    service = get_wearable_service()
    summary = service.get_vitals_summary(user_id="<uuid>", days=7)
    wearable_dict = summary.to_context_dict()

    # Pass to context builder
    build_context(..., wearable_data=wearable_dict)
"""

from .models import (
    IngestionResult,
    MetricSummary,
    VitalReading,
    VitalsBatch,
    VitalsSummary,
)
from .service import WearableService, get_wearable_service

__all__ = [
    # Factory
    "get_wearable_service",
    # Service
    "WearableService",
    # Models
    "VitalReading",
    "VitalsBatch",
    "VitalsSummary",
    "MetricSummary",
    "IngestionResult",
]
