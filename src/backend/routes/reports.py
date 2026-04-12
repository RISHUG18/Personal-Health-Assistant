"""HTTP routes for report ingestion, status polling, and legacy step endpoints.

Pipeline Architecture
---------------------
ALL processing uses: Tesseract OCR (text extraction) → Gemini AI (lab result parsing)
Gemini is NEVER used for OCR/vision — only for parsing structured data from OCR text.

Endpoints
---------
POST /reports/ingest              ← RECOMMENDED — async upload + Tesseract + Gemini
GET  /reports/status/{id}         ← poll async pipeline progress
GET  /reports/{id}/lab-results    ← retrieve extracted lab results
GET  /reports                     ← list all reports for the authenticated user
POST /reports/upload              ← upload only (no OCR/extraction)
POST /reports/ocr                 ← run Tesseract OCR on an already-uploaded report
POST /reports/extract-labs        ← run Gemini extraction on a report's stored OCR text
POST /reports/extract-labs-gemini ← alias of extract-labs (legacy compat)
POST /reports/process             ← synchronous full pipeline (upload + Tesseract + Gemini)
"""
import logging
import os
from urllib.parse import unquote, urlparse

from fastapi import (
    APIRouter, BackgroundTasks, Depends, File, Form,
    HTTPException, Query, UploadFile, status,
)
from pydantic import BaseModel, Field

from backend.config.supabase_client import (
    get_ocr_reports_table,
    get_reports_bucket,
    get_supabase_client,
)
from backend.controllers.reports_controller import (
    ReportOCRError,
    ReportUploadError,
    create_pending_report,
    delete_report_for_user,
    run_full_pipeline_background,
    upload_medical_report,
)
from backend.services.reports_service import (
    ReportDeletionForbiddenError,
    ReportDeletionNotFoundError,
    ReportDeletionServiceError,
)
from backend.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])
api_reports_router = APIRouter(prefix="/api/reports", tags=["reports"])
_log = logging.getLogger(__name__)


class DeleteReportResponse(BaseModel):
    """Response payload for report deletion endpoints."""

    message: str = Field(..., description="Deletion outcome message")
    report_id: str = Field(..., description="Deleted report UUID")
    alerts_deleted: int = Field(..., ge=0, description="Number of linked alerts removed")
    deleted_at: str = Field(..., description="UTC timestamp when deletion completed")


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


def _normalize_signed_url(raw_value: str) -> str:
    """Normalize signed URL payloads that may be absolute or relative."""
    candidate = (raw_value or "").strip()
    if not candidate:
        return ""

    if candidate.startswith("http://") or candidate.startswith("https://"):
        return candidate

    supabase_url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    if not supabase_url:
        return candidate

    if candidate.startswith("/storage/v1/"):
        return f"{supabase_url}{candidate}"
    if candidate.startswith("/"):
        return f"{supabase_url}/storage/v1{candidate}"
    return candidate


def _extract_signed_url(payload: object) -> str | None:
    """Extract signed URL from supabase-py responses across minor versions."""
    if isinstance(payload, str):
        normalized = _normalize_signed_url(payload)
        return normalized or None

    if isinstance(payload, dict):
        for key in ("signed_url", "signedUrl", "signedURL", "url"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                normalized = _normalize_signed_url(value)
                return normalized or None

        nested = payload.get("data")
        if isinstance(nested, dict):
            for key in ("signed_url", "signedUrl", "signedURL", "url"):
                value = nested.get(key)
                if isinstance(value, str) and value.strip():
                    normalized = _normalize_signed_url(value)
                    return normalized or None

    return None


def _get_owned_report_or_404(client, table: str, report_id: str, user_id: str) -> dict:
    """Fetch a report only if it belongs to the authenticated user."""
    try:
        resp = (
            client.table(table)
            .select(
                "id, user_id, source_file_name, source_url, storage_path, "
                "processing_status, processing_error, ocr_confidence"
            )
            .eq("id", report_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        error_text = str(exc)
        if "PGRST204" in error_text or "storage_path" in error_text:
            resp = (
                client.table(table)
                .select(
                    "id, user_id, source_file_name, source_url, "
                    "processing_status, processing_error, ocr_confidence"
                )
                .eq("id", report_id)
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch report metadata: {exc}",
            ) from exc

    rows = resp.data or []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    return rows[0]


# ═══════════════════════════════════════════════════════════════════════════════
# POST /reports/ingest  — RECOMMENDED: full async pipeline
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_report(
    background_tasks: BackgroundTasks,
    user_id: str = Form(..., description="UUID of the report owner"),
    user_name: str = Form(None, description="Display name (e.g. 'Arjun Sharma')"),
    file: UploadFile = File(..., description="Medical report PDF or image"),
    current_user: str = Depends(get_current_user),
):
    """Upload a PDF/image and run Tesseract OCR + Gemini extraction automatically.

    Returns HTTP 202 immediately with a ``report_id``.
    OCR (Tesseract) and lab extraction (Gemini reads OCR text) run in the background.

    Pipeline stages (``medical_reports.processing_status``):
    - ``pending``      — uploaded, waiting for Tesseract
    - ``ocr_complete`` — Tesseract done, Gemini parsing starting
    - ``done``         — lab results written to ``lab_results``
    - ``failed``       — see ``processing_error``
    """
    if user_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload reports for another user",
        )

    file_bytes = await file.read()
    client = get_supabase_client()
    bucket = get_reports_bucket()
    table = get_ocr_reports_table()

    try:
        storage_path, public_url = upload_medical_report(
            client=client, bucket=bucket, user_id=user_id,
            original_filename=file.filename or "report.pdf",
            file_bytes=file_bytes,
            content_type=file.content_type or "application/pdf",
            user_name=user_name,
        )
    except ReportUploadError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err

    try:
        report_id = create_pending_report(
            client=client, table=table, user_id=user_id,
            storage_path=storage_path, public_url=public_url,
            source_file_name=file.filename or "report.pdf",
        )
    except ReportUploadError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err

    background_tasks.add_task(
        run_full_pipeline_background,
        client, bucket, table, user_id, storage_path, report_id,
    )

    return {
        "report_id": report_id,
        "storage_path": storage_path,
        "public_url": public_url,
        "processing_status": "pending",
        "message": "Report queued. Poll GET /reports/status/{report_id} for progress.",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# GET /reports  — list reports for authenticated user (Android report history)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("", status_code=status.HTTP_200_OK)
async def list_user_reports(
    user_id: str = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Return a paginated list of medical reports for the given user.

    Used by the Android app's report history screen.

    Response shape matches the Android ``ReportsListResponse`` model:
    ``{ items: [...], total, limit, offset }``
    """
    client = get_supabase_client()
    table = get_ocr_reports_table()

    try:
        resp = (
            client.table(table)
            .select(
                "id, source_file_name, source_url, report_type, report_date, "
                "processing_status, ocr_confidence, created_at",
                count="exact",
            )
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch reports: {exc}",
        ) from exc

    return {
        "items": resp.data or [],
        "total": resp.count or 0,
        "limit": limit,
        "offset": offset,
    }


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_200_OK,
    response_model=DeleteReportResponse,
)
@api_reports_router.delete(
    "/{report_id}",
    status_code=status.HTTP_200_OK,
    response_model=DeleteReportResponse,
)
async def delete_report(report_id: str, user_id: str = Depends(get_current_user)):
    """Delete a report and clean up linked DB rows and storage artifacts."""
    try:
        return delete_report_for_user(report_id=report_id, user_id=user_id)
    except ReportOCRError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ReportDeletionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ReportDeletionForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ReportDeletionServiceError as exc:
        _log.error("Failed to delete report %s for user %s: %s", report_id, user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete report",
        ) from exc


# ═══════════════════════════════════════════════════════════════════════════════
# GET /reports/status/{report_id}  — poll pipeline progress
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/status/{report_id}", status_code=status.HTTP_200_OK)
async def get_report_status(report_id: str, user_id: str = Depends(get_current_user)):
    """Return the current Tesseract→Gemini pipeline status for a report.

    Fields:
    - ``processing_status``: ``pending | ocr_complete | done | failed``
    - ``processing_error``:  non-null only when status is ``failed``
    - ``ocr_confidence``:    Tesseract average confidence (0–100)
    - ``lab_results_count``: number of extracted lab rows (only when ``done``)
    """
    client = get_supabase_client()
    table = get_ocr_reports_table()

    row = _get_owned_report_or_404(client, table, report_id, user_id)
    lab_results_count: int | None = None
    if row.get("processing_status") == "done":
        try:
            count_resp = (
                client.table("lab_results")
                .select("id", count="exact")
                .eq("report_id", report_id)
                .execute()
            )
            lab_results_count = count_resp.count
        except Exception:  # noqa: BLE001
            pass

    return {
        "report_id": report_id,
        "source_file_name": row.get("source_file_name"),
        "processing_status": row.get("processing_status"),
        "processing_error": row.get("processing_error"),
        "ocr_confidence": row.get("ocr_confidence"),
        "lab_results_count": lab_results_count,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# GET /reports/{report_id}/lab-results  — retrieve extracted lab results
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/{report_id}/lab-results", status_code=status.HTTP_200_OK)
async def get_lab_results(report_id: str, user_id: str = Depends(get_current_user)):
    """Return all structured lab results extracted from a report by Gemini.

    Available once ``processing_status == done``.
    """
    client = get_supabase_client()
    table = get_ocr_reports_table()
    _get_owned_report_or_404(client, table, report_id, user_id)

    try:
        resp = (
            client.table("lab_results")
            .select("id, test_name, value, text_value, unit, reference_range, abnormal_flag, extracted_from_page")
            .eq("report_id", report_id)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch lab results: {exc}",
        ) from exc

    # Map the dual-column schema into a single value string for Android
    processed_rows = []
    for row in (resp.data or []):
        final_value = None
        if row.get("value") is not None:
            final_value = str(row["value"])
        elif row.get("text_value") is not None:
            final_value = str(row["text_value"])
            
        processed_rows.append({
            "id": row["id"],
            "test_name": row["test_name"],
            "value": final_value,
            "unit": row["unit"],
            "reference_range": row["reference_range"],
            "abnormal_flag": row["abnormal_flag"],
            "extracted_from_page": row["extracted_from_page"],
        })

    return {
        "report_id": report_id,
        "count": len(processed_rows),
        "lab_results": processed_rows,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# GET /reports/{report_id}/download_url  — generate private signed URL
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/{report_id}/download_url", status_code=status.HTTP_200_OK)
async def get_report_download_url(
    report_id: str,
    user_id: str = Depends(get_current_user),
):
    """Return a short-lived signed URL for downloading a private report PDF.

    Authorization is enforced by matching both ``report_id`` and ``user_id`` so
    users cannot request signed URLs for reports they do not own.
    """
    client = get_supabase_client()
    table = get_ocr_reports_table()
    bucket = get_reports_bucket()

    report_row = _get_owned_report_or_404(client, table, report_id, user_id)
    storage_path = report_row.get("storage_path")
    if not storage_path:
        storage_path = _extract_storage_path_from_source_url(
            report_row.get("source_url") or "",
            bucket,
        )

    if not storage_path:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Report storage path is unavailable",
        )

    try:
        signed_payload = client.storage.from_(bucket).create_signed_url(storage_path, 60)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate signed URL: {exc}",
        ) from exc

    signed_url = _extract_signed_url(signed_payload)
    if not signed_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Signed URL generation returned an invalid response",
        )

    return {"signed_url": signed_url}

