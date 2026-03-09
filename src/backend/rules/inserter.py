"""Persists evaluated AlertRecord objects to Supabase tables.

The public API is a single function:

    persist_alerts(client, user_id, alerts) -> summary_dict

It is idempotent: old alerts for the user are deleted before new ones are
written.  Because ``alert_evidence`` has ON DELETE CASCADE on ``alert_id``,
deleting an alert row automatically removes its evidence.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List

from backend.rules.models import AlertRecord


def persist_alerts(
    *,
    client: Any,
    user_id: str,
    alerts: List[AlertRecord],
) -> Dict[str, Any]:
    """Delete previous alerts for *user_id* and insert the new ones.

    Args:
        client:   A Supabase ``Client`` instance (from ``get_supabase_client()``).
        user_id:  UUID string identifying the user whose alerts are being refreshed.
        alerts:   List of :class:`~backend.rules.models.AlertRecord` objects
                  returned by :func:`~backend.rules.engine.evaluate_rules`.
                  Only records with ``triggered=True`` are written to the DB.

    Returns:
        A dict with the following keys:

        * ``"deleted"``          – number of alert rows removed
        * ``"inserted"``         – number of new alert rows written
        * ``"evidence_inserted"``– number of ``alert_evidence`` rows written
        * ``"errors"``           – list of error strings (empty on full success)
    """
    errors:            list[str] = []
    deleted:           int = 0
    inserted:          int = 0
    evidence_inserted: int = 0

    # ── 1. Delete all existing alerts for the user ───────────────────────────
    # The ON DELETE CASCADE constraint on alert_evidence means evidence rows
    # are removed automatically.
    try:
        del_resp = (
            client.table("alerts")
            .delete()
            .eq("user_id", user_id)
            .execute()
        )
        deleted = len(del_resp.data or [])
    except Exception as exc:
        errors.append(f"delete_alerts: {exc}")
        return {"deleted": 0, "inserted": 0, "evidence_inserted": 0, "errors": errors}

    # ── 2. Insert triggered alerts and their evidence ────────────────────────
    for alert in alerts:
        if not alert.triggered:
            continue

        alert_id = str(uuid.uuid4())
        severity = alert.severity.value if alert.severity else None
        reason   = alert.reason or alert.rule_id

        # -- Insert the alert row --
        try:
            client.table("alerts").insert(
                {
                    "id":       alert_id,
                    "user_id":  user_id,
                    "severity": severity,
                    "reason":   reason,
                }
            ).execute()
            inserted += 1
        except Exception as exc:
            errors.append(f"insert_alert({alert.rule_id}): {exc}")
            continue  # skip evidence for this alert

        # -- Insert one evidence row per LabRow that triggered this alert --
        for row in alert.evidence:
            ev_id = str(uuid.uuid4())
            try:
                client.table("alert_evidence").insert(
                    {
                        "id":               ev_id,
                        "alert_id":         alert_id,
                        "report_id":        getattr(row, "report_id",       None),
                        "lab_result_id":    getattr(row, "lab_result_id",   None),
                        "ocr_text_snippet": getattr(row, "ocr_snippet",     None),
                    }
                ).execute()
                evidence_inserted += 1
            except Exception as exc:
                errors.append(f"insert_evidence({alert.rule_id}): {exc}")

    return {
        "deleted":           deleted,
        "inserted":          inserted,
        "evidence_inserted": evidence_inserted,
        "errors":            errors,
    }
