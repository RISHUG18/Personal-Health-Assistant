"""Report repository helpers for direct database operations."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote, urlparse

from supabase import Client

from backend.services.retrieval.indexer import remove_report_index


_log = logging.getLogger(__name__)


class ReportRepositoryError(RuntimeError):
    """Raised when report persistence operations fail."""


class ReportNotFoundError(ReportRepositoryError):
    """Raised when the requested report does not exist."""


class ReportForbiddenError(ReportRepositoryError):
    """Raised when the caller does not own the requested report."""


@dataclass(frozen=True)
class ReportCascadeDeleteResult:
    """Result of deleting a report and related rows."""

    report_id: str
    alerts_deleted: int


def _extract_rows(response: Any) -> list[dict]:
    rows = getattr(response, "data", None)
    return rows or []


def _is_missing_relation_error(exc: Exception) -> bool:
    error_text = str(exc).lower()
    return "relation" in error_text and "does not exist" in error_text


def _is_missing_column_error(exc: Exception) -> bool:
    error_text = str(exc).lower()
    return (
        "column" in error_text and "does not exist" in error_text
    ) or "pgrst204" in error_text


def _unique_non_empty_strings(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)

    return result


def _coerce_json_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value

    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None

    return None


def _extract_storage_path_from_source_url(source_url: str, bucket: str) -> str | None:
    """Best-effort extraction of storage path from a Supabase object URL."""
    if not source_url:
        return None

    path = urlparse(source_url).path
    if not path:
        return None

    markers = (
        f"/object/public/{bucket}/",
        f"/object/sign/{bucket}/",
        f"/object/{bucket}/",
    )
    for marker in markers:
        marker_index = path.find(marker)
        if marker_index >= 0:
            raw_path = path[marker_index + len(marker):].lstrip("/")
            return unquote(raw_path) if raw_path else None

    return None


def _json_contains_report_id(payload: Any, report_id: str) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key == "report_id" and str(value) == report_id:
                return True
            if _json_contains_report_id(value, report_id):
                return True
        return False

    if isinstance(payload, list):
        return any(_json_contains_report_id(item, report_id) for item in payload)

    return False


def _fetch_alert_ids_from_alert_evidence(
    client: Client,
    report_id: str,
) -> list[str]:
    evidence_rows = _extract_rows(
        client.table("alert_evidence")
        .select("alert_id")
        .eq("report_id", report_id)
        .execute()
    )
    return _unique_non_empty_strings([row.get("alert_id") for row in evidence_rows])


def _fetch_alert_ids_from_alert_report_column(
    client: Client,
    report_id: str,
    user_id: str,
) -> list[str]:
    alert_rows = _extract_rows(
        client.table("alerts")
        .select("id")
        .eq("user_id", user_id)
        .eq("report_id", report_id)
        .execute()
    )
    return _unique_non_empty_strings([row.get("id") for row in alert_rows])


def _fetch_alert_ids_from_json_evidence(
    client: Client,
    report_id: str,
    user_id: str,
) -> list[str]:
    alert_rows = _extract_rows(
        client.table("alerts")
        .select("id, evidence")
        .eq("user_id", user_id)
        .execute()
    )

    related_ids: list[str] = []
    for row in alert_rows:
        evidence = _coerce_json_value(row.get("evidence"))
        if evidence is None:
            continue
        if _json_contains_report_id(evidence, report_id):
            related_ids.append(row.get("id"))

    return _unique_non_empty_strings(related_ids)


def _scope_alert_ids_to_owner(
    client: Client,
    candidate_alert_ids: list[str],
    user_id: str,
) -> list[str]:
    if not candidate_alert_ids:
        return []

    owned_alert_rows = _extract_rows(
        client.table("alerts")
        .select("id")
        .eq("user_id", user_id)
        .in_("id", candidate_alert_ids)
        .execute()
    )
    return _unique_non_empty_strings([row.get("id") for row in owned_alert_rows])


def _resolve_related_alert_ids(
    client: Client,
    report_id: str,
    user_id: str,
) -> list[str]:
    """Resolve alert IDs linked to a report across multiple schema variants."""
    candidate_ids: list[str] = []

    # Preferred schema: alert_evidence rows carry report_id and point to alerts.
    try:
        candidate_ids = _fetch_alert_ids_from_alert_evidence(client, report_id)
    except Exception as exc:
        if not (_is_missing_relation_error(exc) or _is_missing_column_error(exc)):
            raise ReportRepositoryError(
                f"Failed to query alert_evidence for report {report_id}: {exc}"
            ) from exc

    # Legacy schema: alerts.report_id exists as a direct scalar foreign key.
    if not candidate_ids:
        try:
            candidate_ids = _fetch_alert_ids_from_alert_report_column(client, report_id, user_id)
        except Exception as exc:
            if not (_is_missing_relation_error(exc) or _is_missing_column_error(exc)):
                raise ReportRepositoryError(
                    f"Failed to query alerts.report_id for report {report_id}: {exc}"
                ) from exc

    # Compatibility fallback: alerts.evidence JSON/JSONB embeds report_id.
    if not candidate_ids:
        try:
            candidate_ids = _fetch_alert_ids_from_json_evidence(client, report_id, user_id)
        except Exception as exc:
            if not (_is_missing_relation_error(exc) or _is_missing_column_error(exc)):
                raise ReportRepositoryError(
                    f"Failed to query alerts JSON evidence for report {report_id}: {exc}"
                ) from exc

    try:
        return _scope_alert_ids_to_owner(
            client=client,
            candidate_alert_ids=candidate_ids,
            user_id=user_id,
        )
    except Exception as exc:
        if _is_missing_relation_error(exc) or _is_missing_column_error(exc):
            return candidate_ids
        raise ReportRepositoryError(
            f"Failed to scope related alerts for report {report_id}: {exc}"
        ) from exc


def delete_report_with_alert_cascade(
    client: Client,
    reports_table: str,
    report_id: str,
    user_id: str,
    bucket: str,
) -> ReportCascadeDeleteResult:
    """Delete a report and all alerts linked to that report.

    This function explicitly removes rows from ``alerts`` before deleting the
    report row to guarantee cascade behavior even when database FK cascade is
    not configured.
    """
    try:
        report_rows = _extract_rows(
            client.table(reports_table)
            .select("id, user_id, storage_path, source_url")
            .eq("id", report_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        if _is_missing_column_error(exc):
            try:
                report_rows = _extract_rows(
                    client.table(reports_table)
                    .select("id, user_id, source_url")
                    .eq("id", report_id)
                    .limit(1)
                    .execute()
                )
            except Exception as nested_exc:
                raise ReportRepositoryError(f"Failed to fetch report: {nested_exc}") from nested_exc
        else:
            raise ReportRepositoryError(f"Failed to fetch report: {exc}") from exc

    if not report_rows:
        raise ReportNotFoundError(f"Report {report_id} was not found")

    owner_id = str(report_rows[0].get("user_id") or "")
    if owner_id != user_id:
        raise ReportForbiddenError("Not authorized to delete this report")

    storage_path = str(report_rows[0].get("storage_path") or "").strip()
    if not storage_path:
        storage_path = _extract_storage_path_from_source_url(
            source_url=str(report_rows[0].get("source_url") or ""),
            bucket=bucket,
        ) or ""

    related_alert_ids = _resolve_related_alert_ids(
        client=client,
        report_id=report_id,
        user_id=user_id,
    )
    alerts_deleted = len(related_alert_ids)

    if related_alert_ids:
        try:
            client.table("alert_evidence").delete().in_("alert_id", related_alert_ids).execute()
        except Exception as exc:
            if not (_is_missing_relation_error(exc) or _is_missing_column_error(exc)):
                raise ReportRepositoryError(
                    f"Failed to delete related alert evidence for report {report_id}: {exc}"
                ) from exc

        try:
            client.table("alerts").delete().eq("user_id", user_id).in_("id", related_alert_ids).execute()
        except Exception as exc:
            if not (_is_missing_relation_error(exc) or _is_missing_column_error(exc)):
                raise ReportRepositoryError(
                    f"Failed to delete related alerts for report {report_id}: {exc}"
                ) from exc

    try:
        client.table("lab_results").delete().eq("report_id", report_id).execute()
    except Exception as exc:
        if not (_is_missing_relation_error(exc) or _is_missing_column_error(exc)):
            raise ReportRepositoryError(
                f"Failed to delete related lab results for report {report_id}: {exc}"
            ) from exc

    try:
        remove_report_index(client=client, report_id=report_id, user_id=user_id)
    except Exception as exc:
        if not (_is_missing_relation_error(exc) or _is_missing_column_error(exc)):
            raise ReportRepositoryError(
                f"Failed to delete report index chunks for report {report_id}: {exc}"
            ) from exc

    if storage_path:
        try:
            client.storage.from_(bucket).remove([storage_path])
        except Exception as exc:
            _log.warning(
                "Failed to remove storage object during report delete report_id=%s path=%s: %s",
                report_id,
                storage_path,
                exc,
            )

    try:
        client.table(reports_table).delete().eq("id", report_id).eq("user_id", user_id).execute()
    except Exception as exc:
        raise ReportRepositoryError(f"Failed to delete report {report_id}: {exc}") from exc

    return ReportCascadeDeleteResult(
        report_id=report_id,
        alerts_deleted=alerts_deleted,
    )
