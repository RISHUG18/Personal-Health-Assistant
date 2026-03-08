"""Persist generated alerts and their evidence to Supabase.

Tables written
--------------
alerts          — one row per triggered alert
alert_evidence  — one or more rows per alert (one per EvidenceRef)

Idempotency
-----------
All existing alerts for the user are deleted before new ones are inserted.
alert_evidence rows cascade-delete when their parent alert is deleted
(enforced by the FK constraint in the schema).

Calling persist_alerts() multiple times for the same user is therefore
safe and always leaves the alerts table in the state produced by the most
recent rule evaluation run.
"""

from __future__ import annotations

import logging
import uuid
from typing import List

from supabase import Client

from .models import AlertRecord

logger = logging.getLogger(__name__)


def persist_alerts(
    client: Client,
    user_id: str,
    alerts: List[AlertRecord],
) -> dict:
    """Write a batch of alerts + evidence to the database.

    Parameters
    ----------
    client:
        Supabase client instance.
    user_id:
        UUID of the user.  Used to scope the delete before re-insert.
    alerts:
        List of AlertRecord objects produced by the engine.

    Returns
    -------
    dict with keys:
        deleted          : int       — old alert rows removed
        inserted         : int       — new alert rows inserted
        evidence_inserted: int       — alert_evidence rows inserted
        errors           : list[str] — non-fatal error descriptions
    """
    errors: List[str] = []

    # ── 1. Delete existing alerts for user (idempotency) ─────────────────────
    # alert_evidence rows are removed automatically via ON DELETE CASCADE.
    deleted = 0
    try:
        del_resp = (
            client.table("alerts")
            .delete()
            .eq("user_id", user_id)
            .execute()
        )
        deleted = len(del_resp.data or [])
        logger.info(
            "Deleted %d existing alert(s) for user_id=%s (evidence cascade-deleted).",
            deleted, user_id,
        )
    except Exception as exc:
        logger.warning(
            "Failed to delete existing alerts for user_id=%s: %s", user_id, exc
        )
        errors.append(f"Delete old alerts failed: {exc}")

    if not alerts:
        logger.info("No alerts to insert for user_id=%s.", user_id)
        return {
            "deleted": deleted,
            "inserted": 0,
            "evidence_inserted": 0,
            "errors": errors,
        }

    # ── 2. Insert alert rows ─────────────────────────────────────────────────
    alert_payload = [
        {
            "id": alert.alert_id,
            "user_id": alert.user_id,
            "severity": alert.severity.value,      # "low" | "medium" | "high"
            "reason": alert.reason,
            "created_at": alert.timestamp.isoformat(),
        }
        for alert in alerts
    ]

    try:
        client.table("alerts").insert(alert_payload).execute()
        logger.info(
            "Inserted %d alert(s) for user_id=%s.", len(alerts), user_id
        )
    except Exception as exc:
        logger.error(
            "Failed to insert alerts for user_id=%s: %s", user_id, exc
        )
        errors.append(f"Insert alerts failed: {exc}")
        # Return early — no point inserting orphan evidence rows
        return {
            "deleted": deleted,
            "inserted": 0,
            "evidence_inserted": 0,
            "errors": errors,
        }

    # ── 3. Build and insert alert_evidence rows ──────────────────────────────
    evidence_payload: List[dict] = []
    for alert in alerts:
        for ref in alert.evidence_refs:
            evidence_payload.append(
                {
                    "id": str(uuid.uuid4()),
                    "alert_id": alert.alert_id,
                    "report_id": ref.report_id,        # may be None
                    "lab_result_id": ref.lab_result_id,  # may be None
                    "ocr_text_snippet": ref.ocr_text_snippet,
                }
            )

    evidence_inserted = 0
    if evidence_payload:
        try:
            client.table("alert_evidence").insert(evidence_payload).execute()
            evidence_inserted = len(evidence_payload)
            logger.info(
                "Inserted %d alert_evidence row(s) for user_id=%s.",
                evidence_inserted, user_id,
            )
        except Exception as exc:
            logger.error(
                "Failed to insert alert_evidence for user_id=%s: %s", user_id, exc
            )
            errors.append(f"Insert alert_evidence failed: {exc}")
    else:
        logger.info(
            "No evidence refs to insert for user_id=%s "
            "(rules with no direct lab-result links, e.g. missing_critical_tests).",
            user_id,
        )

    return {
        "deleted": deleted,
        "inserted": len(alerts),
        "evidence_inserted": evidence_inserted,
        "errors": errors,
    }
