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
from fastapi import (
    APIRouter, BackgroundTasks, Depends, File, Form,
    HTTPException, Query, UploadFile, status,
)

from backend.config.supabase_client import (
    get_ocr_reports_table,
    get_reports_bucket,
    get_supabase_client,
)
from backend.controllers.reports_controller import (
    ReportUploadError,
    create_pending_report,
    run_full_pipeline_background,
    upload_medical_report,
)
from backend.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])


# ═══════════════════════════════════════════════════════════════════════════════
# POST /reports/ingest  — RECOMMENDED: full async pipeline
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_report(
    background_tasks: BackgroundTasks,
    user_id: str = Form(..., description="UUID of the report owner"),
    user_name: str = Form(None, description="Display name (e.g. 'Arjun Sharma')"),
    file: UploadFile = File(..., description="Medical report PDF or image"),
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


# ═══════════════════════════════════════════════════════════════════════════════
# GET /reports/status/{report_id}  — poll pipeline progress
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/status/{report_id}", status_code=status.HTTP_200_OK)
async def get_report_status(report_id: str):
    """Return the current Tesseract→Gemini pipeline status for a report.

    Fields:
    - ``processing_status``: ``pending | ocr_complete | done | failed``
    - ``processing_error``:  non-null only when status is ``failed``
    - ``ocr_confidence``:    Tesseract average confidence (0–100)
    - ``lab_results_count``: number of extracted lab rows (only when ``done``)
    """
    client = get_supabase_client()
    table = get_ocr_reports_table()

    try:
        resp = (
            client.table(table)
            .select("id, processing_status, processing_error, ocr_confidence, source_file_name")
            .eq("id", report_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DB lookup failed: {exc}",
        ) from exc

    rows = resp.data or []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No report found with id={report_id}",
        )

    row = rows[0]
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
async def get_lab_results(report_id: str):
    """Return all structured lab results extracted from a report by Gemini.

    Available once ``processing_status == done``.
    """
    client = get_supabase_client()

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


