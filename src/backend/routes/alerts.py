"""HTTP routes for alert evaluation and retrieval.

Endpoints
---------
POST /alerts/evaluate?user_id=<uuid>
    Run all rules against the user's lab data, persist results.
    Returns a detailed summary of what fired and what was inserted.

GET /alerts/list?user_id=<uuid>
    Retrieve current alerts for a user with embedded evidence.

GET /alerts/rules
    List all registered rules (rule_id, description, tags).
    Useful for UI / debugging — no DB access required.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, status

from backend.config.supabase_client import get_supabase_client
from backend.rules import ALL_RULES, evaluate_rules, persist_alerts

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])


# ── POST /alerts/evaluate ─────────────────────────────────────────────────────


@router.post("/evaluate", status_code=status.HTTP_200_OK)
async def evaluate_user_alerts(
    user_id: str = Query(..., description="UUID of the user to evaluate rules for"),
):
    """Run all rules against the user's lab data and persist generated alerts.

    Steps performed
    ---------------
    1. Fetch all ``medical_reports`` for the user (report metadata + OCR text).
    2. Fetch all ``lab_results`` linked to those reports.
    3. Evaluate each of the 13 registered rules against the fetched rows.
    4. Delete the user's existing alerts (idempotency), then insert new ones.
    5. Insert ``alert_evidence`` rows linking each alert to specific lab rows.

    Returns a summary that includes every triggered rule, its severity,
    and the generated ``alert_id`` so the client can reference it.
    """
    client = get_supabase_client()

    # ── Evaluate ──────────────────────────────────────────────────────────────
    logger.info("Starting rule evaluation for user_id=%s", user_id)
    try:
        alerts = evaluate_rules(client=client, user_id=user_id)
    except Exception as exc:
        logger.error("Rule evaluation failed for user_id=%s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rule evaluation failed: {exc}",
        ) from exc

    # ── Persist ───────────────────────────────────────────────────────────────
    logger.info(
        "Persisting %d alert(s) for user_id=%s", len(alerts), user_id
    )
    try:
        persist_result = persist_alerts(client=client, user_id=user_id, alerts=alerts)
    except Exception as exc:
        logger.error("Alert persistence failed for user_id=%s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Alert persistence failed: {exc}",
        ) from exc

    # ── Build response ────────────────────────────────────────────────────────
    triggered_summary = [
        {
            "alert_id": a.alert_id,
            "severity": a.severity.value,
            "reason": a.reason,
            "evidence_count": len(a.evidence_refs),
            "timestamp": a.timestamp.isoformat(),
        }
        for a in alerts
    ]

    response = {
        "user_id": user_id,
        "rules_evaluated": len(ALL_RULES),
        "rules_triggered": len(alerts),
        "alerts_inserted": persist_result["inserted"],
        "evidence_inserted": persist_result["evidence_inserted"],
        "old_alerts_deleted": persist_result["deleted"],
        "errors": persist_result["errors"],
        "triggered_alerts": triggered_summary,
    }

    logger.info(
        "Evaluation complete for user_id=%s: %d triggered, %d inserted, %d evidence rows",
        user_id, len(alerts), persist_result["inserted"], persist_result["evidence_inserted"],
    )
    return response


# ── GET /alerts/list ──────────────────────────────────────────────────────────


@router.get("/list", status_code=status.HTTP_200_OK)
async def list_user_alerts(
    user_id: str = Query(..., description="UUID of the user"),
):
    """Return all current alerts for a user, with embedded evidence rows.

    Alerts are ordered newest-first.  Each alert object includes an
    ``evidence`` array with the supporting ``alert_evidence`` rows.
    """
    client = get_supabase_client()

    # Fetch alerts
    try:
        alert_resp = (
            client.table("alerts")
            .select("id, severity, reason, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as exc:
        logger.error("Failed to fetch alerts for user_id=%s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch alerts: {exc}",
        ) from exc

    alert_list = alert_resp.data or []

    # Enrich each alert with its evidence rows
    results = []
    for alert in alert_list:
        try:
            ev_resp = (
                client.table("alert_evidence")
                .select("id, report_id, lab_result_id, ocr_text_snippet")
                .eq("alert_id", alert["id"])
                .execute()
            )
            evidence = ev_resp.data or []
        except Exception as exc:
            logger.warning(
                "Failed to fetch evidence for alert_id=%s: %s", alert["id"], exc
            )
            evidence = []

        results.append({**alert, "evidence": evidence})

    return {
        "user_id": user_id,
        "alert_count": len(results),
        "alerts": results,
    }


# ── GET /alerts/rules ─────────────────────────────────────────────────────────


@router.get("/rules", status_code=status.HTTP_200_OK)
async def list_registered_rules():
    """Return the full catalogue of registered rules.

    No database access — reads the in-memory rule registry.
    Useful for documentation, admin UIs, and debugging.
    """
    return {
        "rule_count": len(ALL_RULES),
        "rules": [
            {
                "rule_id": r.rule_id,
                "description": r.description,
                "tags": r.tags,
            }
            for r in ALL_RULES
        ],
    }
