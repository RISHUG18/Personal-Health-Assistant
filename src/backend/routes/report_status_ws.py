"""WebSocket route for report processing status subscriptions."""

from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.config.supabase_client import get_ocr_reports_table, get_supabase_client
from backend.services.report_status_ws import (
    build_status_message,
    report_status_connection_manager,
)

router = APIRouter(tags=["report-status-websocket"])
logger = logging.getLogger(__name__)


def _normalize_confidence(raw_confidence: object) -> float | None:
    """Return a normalized confidence in 0.0-1.0 if present/valid."""
    if raw_confidence is None:
        return None
    try:
        confidence = float(raw_confidence)
    except (TypeError, ValueError):
        return None

    if 0.0 <= confidence <= 1.0:
        return round(confidence, 4)

    return round(min(max(confidence, 0.0), 100.0) / 100.0, 4)


def _map_db_status_to_ws(db_status: str | None) -> str:
    """Map persisted DB status values to websocket protocol statuses."""
    normalized = (db_status or "").strip().lower()
    mapping = {
        "pending": "processing",
        "ocr_complete": "validating",
        "done": "completed",
        "failed": "failed",
        "processing": "processing",
        "validating": "validating",
        "completed": "completed",
    }
    return mapping.get(normalized, "processing")


async def _send_status_snapshot_if_available(websocket: WebSocket, report_id: str) -> None:
    """Immediately push latest known status so late subscribers don't miss completion."""
    client = get_supabase_client()
    table = get_ocr_reports_table()

    try:
        response = (
            client.table(table)
            .select("id, processing_status, processing_error, ocr_confidence")
            .eq("id", report_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        # Older schemas may not have processing_status.
        exc_text = str(exc)
        if "processing_status" in exc_text or "PGRST204" in exc_text:
            cached = await report_status_connection_manager.get_last_update(report_id)
            if cached:
                await websocket.send_json(cached)
            return
        logger.debug("Could not load report status snapshot for %s: %s", report_id, exc)
        cached = await report_status_connection_manager.get_last_update(report_id)
        if cached:
            await websocket.send_json(cached)
        return

    rows = response.data or []
    if not rows:
        cached = await report_status_connection_manager.get_last_update(report_id)
        if cached:
            await websocket.send_json(cached)
        return

    row = rows[0]
    ws_status = _map_db_status_to_ws(row.get("processing_status"))
    confidence = _normalize_confidence(row.get("ocr_confidence"))

    data: dict = {}
    error: dict = {}

    if ws_status == "completed":
        tests_detected = 0
        try:
            count_resp = (
                client.table("lab_results")
                .select("id", count="exact")
                .eq("report_id", report_id)
                .execute()
            )
            tests_detected = int(count_resp.count or 0)
        except Exception:  # noqa: BLE001
            pass

        data = {"report_id": report_id, "tests_detected": tests_detected}
        if confidence is not None:
            data["ocr_confidence"] = confidence

    if ws_status == "failed":
        error = {"reason": row.get("processing_error") or "Processing failed"}
        if confidence is not None:
            error["confidence"] = confidence

    await websocket.send_json(
        build_status_message(
            report_id=report_id,
            status=ws_status,
            data=data,
            error=error,
        )
    )


@router.websocket("/ws/report-status/{report_id}")
async def report_status_websocket(websocket: WebSocket, report_id: str) -> None:
    """Keep a live WebSocket open for report status updates."""
    await report_status_connection_manager.connect(report_id, websocket)
    try:
        await _send_status_snapshot_if_available(websocket, report_id)
        # Keep the connection alive. Incoming messages are ignored for now.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await report_status_connection_manager.disconnect(report_id, websocket)
