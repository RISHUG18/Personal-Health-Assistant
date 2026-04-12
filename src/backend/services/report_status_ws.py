"""WebSocket connection manager for report processing status updates."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ReportStatusConnectionManager:
    """Manage report-scoped WebSocket connections safely across async tasks."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
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
