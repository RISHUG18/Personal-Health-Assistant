"""Service layer for report lifecycle operations."""

from __future__ import annotations

from datetime import datetime, timezone

from backend.config.supabase_client import (
    get_ocr_reports_table,
    get_reports_bucket,
    get_supabase_client,
)
from backend.services.reports_repository import (
    ReportForbiddenError,
    ReportNotFoundError,
    ReportRepositoryError,
    delete_report_with_alert_cascade,
)


class ReportDeletionServiceError(RuntimeError):
    """Raised when deleting a report fails at the service layer."""


class ReportDeletionNotFoundError(ReportDeletionServiceError):
    """Raised when the report does not exist."""


class ReportDeletionForbiddenError(ReportDeletionServiceError):
    """Raised when a user attempts to delete another user's report."""


def delete_report_and_related_alerts(report_id: str, user_id: str) -> dict:
    """Delete a report and cascade-delete alerts linked to the report.

    Returns a response-ready payload with counts and deletion timestamp.
    """
    client = get_supabase_client()
    reports_table = get_ocr_reports_table()
    reports_bucket = get_reports_bucket()

    try:
        deletion_result = delete_report_with_alert_cascade(
            client=client,
            reports_table=reports_table,
            report_id=report_id,
            user_id=user_id,
            bucket=reports_bucket,
        )
    except ReportNotFoundError as exc:
        raise ReportDeletionNotFoundError(str(exc)) from exc
    except ReportForbiddenError as exc:
        raise ReportDeletionForbiddenError(str(exc)) from exc
    except ReportRepositoryError as exc:
        raise ReportDeletionServiceError(str(exc)) from exc

    return {
        "message": "Report deleted successfully",
        "report_id": deletion_result.report_id,
        "alerts_deleted": deletion_result.alerts_deleted,
        "deleted_at": datetime.now(timezone.utc).isoformat(),
    }
