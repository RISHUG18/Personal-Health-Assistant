"""WebSocket route for report processing status subscriptions."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.report_status_ws import report_status_connection_manager

router = APIRouter(tags=["report-status-websocket"])


@router.websocket("/ws/report-status/{report_id}")
async def report_status_websocket(websocket: WebSocket, report_id: str) -> None:
    """Keep a live WebSocket open for report status updates."""
    await report_status_connection_manager.connect(report_id, websocket)
    try:
        # Keep the connection alive. Incoming messages are ignored for now.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await report_status_connection_manager.disconnect(report_id, websocket)
