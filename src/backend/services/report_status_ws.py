"""WebSocket connection manager for report processing status updates.

Cross-process Status Delivery
-------------------------------
When workers run as separate Celery processes they cannot call this
in-memory manager directly.  Instead they publish JSON messages to the
Redis pub/sub channel ``report:status:<report_id>``.

The API process runs a single background asyncio task
(:func:`start_redis_subscriber`) that listens on the pattern
``report:status:*``.  Every message received is forwarded to all
WebSocket clients that are currently connected for that report.

If Redis is not configured (``REDIS_URL`` env var absent or Redis is
unreachable) the subscriber is silently skipped and the system falls
back to the existing in-process :class:`ReportStatusConnectionManager`
(which still works correctly when using FastAPI ``BackgroundTasks``).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections import OrderedDict, defaultdict
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ReportStatusConnectionManager:
    """Manage report-scoped WebSocket connections safely across async tasks."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._last_update_by_report: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._max_cached_updates = 2048
        self._lock = asyncio.Lock()

    async def connect(self, report_id: str, websocket: WebSocket) -> None:
        """Accept and register a WebSocket for a report."""
        await websocket.accept()
        async with self._lock:
            self._connections[report_id].add(websocket)

    async def disconnect(self, report_id: str, websocket: WebSocket) -> None:
        """Remove a WebSocket and clean up empty report buckets."""
        async with self._lock:
            sockets = self._connections.get(report_id)
            if not sockets:
                return

            sockets.discard(websocket)
            if not sockets:
                self._connections.pop(report_id, None)

    async def send_update(self, report_id: str, message: dict[str, Any]) -> None:
        """Broadcast a status update to all subscribers for a report."""
        async with self._lock:
            self._last_update_by_report[report_id] = message
            self._last_update_by_report.move_to_end(report_id)
            while len(self._last_update_by_report) > self._max_cached_updates:
                self._last_update_by_report.popitem(last=False)

            sockets = list(self._connections.get(report_id, set()))

        if not sockets:
            return

        stale: list[WebSocket] = []
        for socket in sockets:
            try:
                await socket.send_json(message)
            except Exception as exc:  # noqa: BLE001
                logger.debug(
                    "Dropping stale WebSocket for report_id=%s: %s",
                    report_id,
                    exc,
                )
                stale.append(socket)

        for socket in stale:
            await self.disconnect(report_id, socket)

    async def get_last_update(self, report_id: str) -> dict[str, Any] | None:
        """Return the most recent status update for a report if cached."""
        async with self._lock:
            return self._last_update_by_report.get(report_id)

    async def start_redis_subscriber(self) -> None:
        """Subscribe to Redis pub/sub and forward messages to WS clients.

        This coroutine is intended to be run as a long-lived asyncio task
        (started in the FastAPI ``startup`` lifecycle hook).  It will:

        1. Connect to Redis using ``REDIS_URL`` (defaults to
           ``redis://localhost:6379/0``).
        2. Pattern-subscribe to ``report:status:*``.
        3. For every message received, call :meth:`send_update` so all
           WebSocket clients connected for that report receive the update.

        If Redis is unavailable the coroutine logs a warning and exits
        silently — the rest of the application continues to work (status
        updates will only reach clients that share the same API process as
        the worker, i.e. FastAPI ``BackgroundTasks`` mode).
        """
        redis_url = os.getenv("REDIS_URL", "")
        if not redis_url:
            logger.info(
                "REDIS_URL not set — Redis status subscriber disabled. "
                "WebSocket updates will only work within a single process."
            )
            return

        try:
            import redis.asyncio as aioredis
        except ImportError:
            logger.warning(
                "redis[asyncio] not installed — Redis subscriber disabled. "
                "Install it with: pip install redis[asyncio]"
            )
            return

        logger.info("Connecting Redis status subscriber to %s …", redis_url)
        retry_delay = 2.0

        while True:
            try:
                async with aioredis.from_url(redis_url, decode_responses=True) as r:
                    pubsub = r.pubsub()
                    await pubsub.psubscribe("report:status:*")
                    logger.info("Redis status subscriber active (pattern: report:status:*)")
                    retry_delay = 2.0  # reset backoff on successful connect

                    async for raw_message in pubsub.listen():
                        # Only handle actual published messages (not subscription confirms)
                        if raw_message.get("type") != "pmessage":
                            continue

                        raw_data = raw_message.get("data")
                        if not raw_data:
                            continue

                        try:
                            message: dict[str, Any] = json.loads(raw_data)
                        except (json.JSONDecodeError, TypeError) as exc:
                            logger.warning("Malformed Redis message: %s — %s", raw_data, exc)
                            continue

                        report_id = message.get("report_id")
                        if not report_id:
                            continue

                        logger.debug(
                            "Redis→WS relay: report_id=%s status=%s",
                            report_id,
                            message.get("status"),
                        )

                        try:
                            from backend.routes.report_status_ws import _map_db_status_to_ws
                            raw_status = message.get("status")
                            status = _map_db_status_to_ws(raw_status)
                        except Exception:
                            continue

                        await self.send_update(
                            report_id,
                            build_status_message(report_id, status),
                        )

            except asyncio.CancelledError:
                logger.info("Redis status subscriber cancelled — shutting down.")
                return
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Redis status subscriber error (retrying in %.0fs): %s",
                    retry_delay,
                    exc,
                )
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60.0)  # exponential backoff, cap 60 s


# Singleton shared by route handlers and background tasks within one process.
report_status_connection_manager = ReportStatusConnectionManager()


def build_status_message(
    report_id: str,
    status: str,
    data: dict[str, Any] | None = None,
    error: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a protocol-compliant report status payload."""
    return {
        "report_id": report_id,
        "status": status,
        "data": data or {},
        "error": error or {},
    }
