"""Environmental data pipeline package.

Public API
----------
``get_environment_service``
    Factory that returns a production-ready :class:`EnvironmentService`
    backed by Open-Meteo APIs and Supabase storage.  This is the only
    import most callers need::

        from backend.services.environment import get_environment_service

        _env = get_environment_service()
        snapshot = _env.get_snapshot_for_coordinates(
            user_id="<uuid>",
            latitude=17.4065,
            longitude=78.4772,
            location_city="Hyderabad",
        )
        env_dict = snapshot.to_context_dict()   # → pass to build_context()

``EnvironmentService``
    The orchestrating service class (useful when you need to inject custom
    clients, e.g. mocks in tests).

``EnvironmentalSnapshot``
    The merged data model returned by ``get_snapshot_for_coordinates()``.

``NullEnvironmentStore``
    No-op store for test environments — install this when you do not want DB
    side-effects during unit tests.
"""

from .models import EnvironmentalSnapshot
from .service import EnvironmentService, get_environment_service
from .store import NullEnvironmentStore

__all__ = [
    "EnvironmentalSnapshot",
    "EnvironmentService",
    "NullEnvironmentStore",
    "get_environment_service",
]
