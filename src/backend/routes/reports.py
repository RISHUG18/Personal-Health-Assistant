"""HTTP routes for report ingestion and status polling.

Endpoints
---------
POST /reports/ingest
    Upload a PDF/image and automatically run Tesseract OCR + Gemini extraction.
    Returns HTTP 202 immediately; processing runs as a background task.

GET /reports/status/{report_id}
    Poll the processing status of a previously ingested report.

GET /reports/{report_id}/lab-results
    Retrieve all structured lab results extracted from a report.
"""
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile, status

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

router = APIRouter(prefix="/reports", tags=["reports"])


# ---------------------------------------------------------------------------
# POST /reports/ingest  — FULL ASYNC PIPELINE (single entry point)
# ---------------------------------------------------------------------------

@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_report(
    background_tasks: BackgroundTasks,
    user_id: str = Form(..., description="UUID of the report owner"),
    user_name: str = Form(None, description="Display name of the user (e.g. 'Arjun Sharma')"),
    file: UploadFile = File(..., description="Medical report PDF or image"),
):
    """Upload a PDF/image and automatically run Tesseract OCR + Gemini extraction.

    **The only recommended endpoint** for uploading and processing reports.

    Upload and initial DB row creation happen synchronously so the client
    receives a ``report_id`` immediately with HTTP 202.  OCR (Tesseract)
    and lab extraction (Gemini) run in the background after the response
    is sent.  Multiple concurrent requests are processed in parallel.

    Poll ``GET /reports/status/{report_id}`` to track progress.

    Pipeline stages stored in ``medical_reports.processing_status``:
    - ``pending``      — uploaded, OCR not yet started
    - ``ocr_complete`` — Tesseract OCR done, Gemini extraction running
    - ``done``         — lab results written to ``lab_results``
    - ``failed``       — see ``processing_error`` for the reason
    """
    file_bytes = await file.read()
    client = get_supabase_client()
    bucket = get_reports_bucket()
    table = get_ocr_reports_table()

    # Step 1 (sync): Upload raw bytes to Supabase Storage.
    try:
        storage_path, public_url = upload_medical_report(
            client=client,
            bucket=bucket,
            user_id=user_id,
            original_filename=file.filename or "report.pdf",
            file_bytes=file_bytes,
            content_type=file.content_type or "application/pdf",
            user_name=user_name,
        )
    except ReportUploadError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err

    # Step 2 (sync): Insert a placeholder DB row — gives client a report_id now.
    try:
        report_id = create_pending_report(
            client=client,
            table=table,
            user_id=user_id,
            storage_path=storage_path,
            public_url=public_url,
            source_file_name=file.filename or "report.pdf",
        )
    except ReportUploadError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err

    # Step 3 (async): Tesseract OCR + Gemini extraction run in background.
    background_tasks.add_task(
        run_full_pipeline_background,
        client,
        bucket,
        table,
        user_id,
        storage_path,
        report_id,
    )

    return {
        "report_id": report_id,
        "storage_path": storage_path,
        "public_url": public_url,
        "processing_status": "pending",
        "message": "Report queued. Poll GET /reports/status/{report_id} for progress.",
    }


# ---------------------------------------------------------------------------
# GET /reports/status/{report_id}  — pipeline progress polling
# ---------------------------------------------------------------------------

@router.get("/status/{report_id}", status_code=status.HTTP_200_OK)
async def get_report_status(report_id: str):
    """Return the current pipeline status for a report.

    Clients should poll this endpoint after calling ``POST /reports/ingest``.

    Response fields:
    - ``processing_status``: ``pending | ocr_complete | done | failed``
    - ``processing_error``: non-null only when status is ``failed``
    - ``ocr_confidence``: Tesseract average confidence (0–100), available once OCR completes
    - ``lab_results_count``: number of rows in ``lab_results`` (only when ``done``)
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

    # Count lab_results rows only when the pipeline is fully done.
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


# ---------------------------------------------------------------------------
# GET /reports/{report_id}/lab-results  — retrieve extracted lab results
# ---------------------------------------------------------------------------

@router.get("/{report_id}/lab-results", status_code=status.HTTP_200_OK)
async def get_lab_results(report_id: str):
    """Return all extracted lab results for a given report.

    Useful for verifying extraction output and for the Android client
    to display structured lab data after the pipeline status is ``done``.
    """
    client = get_supabase_client()

    try:
        resp = (
            client.table("lab_results")
            .select("id, test_name, value, unit, reference_range, abnormal_flag, extracted_from_page")
            .eq("report_id", report_id)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch lab results: {exc}",
        ) from exc

    rows = resp.data or []
    return {
        "report_id": report_id,
        "count": len(rows),
        "lab_results": rows,
    }
