"""Privacy-focused account deletion and data export helpers."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from supabase import Client

from backend.config.supabase_client import (
    get_ocr_reports_table,
    get_reports_bucket,
    get_supabase_client,
)

logger = logging.getLogger(__name__)


class PrivacyOperationError(RuntimeError):
    """Raised when a privacy operation cannot be completed."""


def _extract_rows(response: Any) -> list[dict]:
    """Return rows from a Supabase response object."""
    rows = getattr(response, "data", None)
    return rows or []


def _is_missing_relation_error(exc: Exception) -> bool:
    """Return True when the exception indicates a missing table/column."""
    error_text = str(exc).lower()
    return (
        "relation" in error_text and "does not exist" in error_text
    ) or "pgrst204" in error_text


def _list_user_storage_paths(client: Client, user_id: str) -> list[str]:
    """Collect distinct report storage paths for a user across known tables."""
    table = get_ocr_reports_table()
    bucket = get_reports_bucket()
    storage_paths: set[str] = set()

    try:
        report_rows = _extract_rows(
            client.table(table)
            .select("storage_path, source_url")
            .eq("user_id", user_id)
            .execute()
        )
        for row in report_rows:
            storage_path = (row.get("storage_path") or "").strip()
            if storage_path:
                storage_paths.add(storage_path)
                continue

            source_url = row.get("source_url") or ""
            marker = f"/object/public/{bucket}/"
            if marker in source_url:
                storage_paths.add(source_url.split(marker, 1)[1])
    except Exception as exc:
        raise PrivacyOperationError(
            f"Failed to enumerate medical report storage paths: {exc}"
        ) from exc

    try:
        structured_rows = _extract_rows(
            client.table("structured_reports")
            .select("storage_path, file_url")
            .eq("user_id", user_id)
            .execute()
        )
        for row in structured_rows:
            storage_path = (row.get("storage_path") or "").strip()
            if storage_path:
                storage_paths.add(storage_path)
                continue

            file_url = row.get("file_url") or ""
            marker = f"/object/public/{bucket}/"
            if marker in file_url:
                storage_paths.add(file_url.split(marker, 1)[1])
    except Exception as exc:
        error_text = str(exc)
        if not _is_missing_relation_error(exc) and "storage_path" not in error_text:
            raise PrivacyOperationError(
                f"Failed to enumerate structured report storage paths: {exc}"
            ) from exc

        if _is_missing_relation_error(exc) and "structured_reports" in error_text.lower():
            structured_rows = []
        else:
            structured_rows = _extract_rows(
                client.table("structured_reports")
                .select("file_url")
                .eq("user_id", user_id)
                .execute()
            )
        for row in structured_rows:
            file_url = row.get("file_url") or ""
            marker = f"/object/public/{bucket}/"
            if marker in file_url:
                storage_paths.add(file_url.split(marker, 1)[1])

    return sorted(storage_paths)


def export_user_data(
    user_id: str,
    client: Optional[Client] = None,
) -> dict[str, Any]:
    """Build a machine-readable export payload for a user."""
    db = client or get_supabase_client()
    table = get_ocr_reports_table()

    try:
        profile_rows = _extract_rows(
            db.table("users").select("*").eq("id", user_id).limit(1).execute()
        )
    except Exception as exc:
        raise PrivacyOperationError(f"Failed to fetch user profile: {exc}") from exc

    if not profile_rows:
        raise PrivacyOperationError(f"User {user_id} was not found.")

    try:
        medical_reports = _extract_rows(
            db.table(table)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as exc:
        raise PrivacyOperationError(f"Failed to fetch medical reports: {exc}") from exc

    report_ids = [row["id"] for row in medical_reports if row.get("id")]

    lab_results: list[dict] = []
    if report_ids:
        try:
            lab_results = _extract_rows(
                db.table("lab_results")
                .select("*")
                .in_("report_id", report_ids)
                .execute()
            )
        except Exception as exc:
            raise PrivacyOperationError(f"Failed to fetch lab results: {exc}") from exc

    datasets: dict[str, Any] = {}
    query_specs = {
        "structured_reports": db.table("structured_reports")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True),
        "health_summaries": db.table("health_summaries")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True),
        "wearable_vitals": db.table("wearable_vitals")
        .select("*")
        .eq("user_id", user_id)
        .order("recorded_at", desc=True),
        "environmental_data": db.table("environmental_data")
        .select("*")
        .eq("user_id", user_id)
        .order("recorded_at", desc=True),
        "alerts": db.table("alerts")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True),
        "doctor_mappings_as_patient": db.table("doctor_patient_mapping")
        .select("*")
        .eq("patient_id", user_id),
        "doctor_mappings_as_doctor": db.table("doctor_patient_mapping")
        .select("*")
        .eq("doctor_id", user_id),
    }

    for name, query in query_specs.items():
        try:
            datasets[name] = _extract_rows(query.execute())
        except Exception as exc:
            if _is_missing_relation_error(exc):
                datasets[name] = []
                continue
            raise PrivacyOperationError(f"Failed to fetch {name}: {exc}") from exc

    alert_ids = [row["id"] for row in datasets["alerts"] if row.get("id")]
    alert_evidence: list[dict] = []
    if alert_ids:
        try:
            alert_evidence = _extract_rows(
                db.table("alert_evidence")
                .select("*")
                .in_("alert_id", alert_ids)
                .execute()
            )
        except Exception as exc:
            if _is_missing_relation_error(exc):
                alert_evidence = []
            else:
                raise PrivacyOperationError(
                    f"Failed to fetch alert evidence: {exc}"
                ) from exc

    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "schema_version": 1,
        "profile": profile_rows[0],
        "medical_reports": medical_reports,
        "lab_results": lab_results,
        "structured_reports": datasets["structured_reports"],
        "health_summaries": datasets["health_summaries"],
        "wearable_vitals": datasets["wearable_vitals"],
        "environmental_data": datasets["environmental_data"],
        "alerts": datasets["alerts"],
        "alert_evidence": alert_evidence,
        "doctor_patient_mapping": {
            "as_patient": datasets["doctor_mappings_as_patient"],
            "as_doctor": datasets["doctor_mappings_as_doctor"],
        },
    }


def export_user_data_bytes(
    user_id: str,
    client: Optional[Client] = None,
) -> bytes:
    """Serialize a user export to pretty JSON bytes."""
    payload = export_user_data(user_id=user_id, client=client)
    return json.dumps(payload, indent=2, default=str, ensure_ascii=True).encode("utf-8")


def delete_user_account(
    user_id: str,
    client: Optional[Client] = None,
) -> dict[str, Any]:
    """Hard-delete a user's storage objects, DB row, and Supabase Auth identity."""
    db = client or get_supabase_client()
    bucket = get_reports_bucket()

    profile_rows = _extract_rows(
        db.table("users").select("id").eq("id", user_id).limit(1).execute()
    )
    if not profile_rows:
        raise PrivacyOperationError(f"User {user_id} was not found.")

    storage_paths = _list_user_storage_paths(db, user_id)
    storage_deleted = 0
    if storage_paths:
        try:
            db.storage.from_(bucket).remove(storage_paths)
            storage_deleted = len(storage_paths)
        except Exception as exc:
            raise PrivacyOperationError(
                f"Failed to delete storage objects for user {user_id}: {exc}"
            ) from exc

    try:
        db.table("users").delete().eq("id", user_id).execute()
    except Exception as exc:
        raise PrivacyOperationError(
            f"Failed to delete database user row for user {user_id}: {exc}"
        ) from exc

    try:
        db.auth.admin.delete_user(user_id)
    except Exception as exc:
        logger.error("Auth deletion failed for user %s after DB deletion: %s", user_id, exc)
        raise PrivacyOperationError(
            f"Database deletion completed, but deleting the auth account failed: {exc}"
        ) from exc

    return {
        "user_id": user_id,
        "storage_objects_deleted": storage_deleted,
        "storage_paths_deleted": storage_paths,
        "deleted_at": datetime.now(timezone.utc).isoformat(),
    }
