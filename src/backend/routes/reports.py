"""HTTP routes for report uploads and the async ingestion pipeline."""
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile, status

from backend.config.supabase_client import (
    get_ocr_reports_table,
    get_reports_bucket,
    get_supabase_client,
)
from backend.controllers.reports_controller import (
    ReportOCRError,
    ReportUploadError,
    create_pending_report,
    extract_labs_with_gemini,
    run_full_pipeline_background,
    run_ocr_on_report,
    upload_medical_report,
)

router = APIRouter(prefix="/reports", tags=["reports"])


# ---------------------------------------------------------------------------
# POST /reports/upload  — storage upload only (Step 1 standalone)
# ---------------------------------------------------------------------------

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_report(
    user_id: str = Form(..., description="UUID of the report owner"),
    file: UploadFile = File(..., description="Medical report PDF or image"),
):
    """Upload a medical report to Supabase Storage and return its path.

    Low-level endpoint — no OCR or extraction is triggered.
    Prefer ``POST /reports/ingest`` for the full automatic pipeline.
    """
    file_bytes = await file.read()
    client = get_supabase_client()
    bucket = get_reports_bucket()

    try:
        storage_path, public_url = upload_medical_report(
            client=client,
            bucket=bucket,
            user_id=user_id,
            original_filename=file.filename or "report.pdf",
            file_bytes=file_bytes,
            content_type=file.content_type or "application/pdf",
        )
    except ReportUploadError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err

    return {"path": storage_path, "public_url": public_url}


# ---------------------------------------------------------------------------
# POST /reports/ocr  — OCR only for an already-uploaded file (Step 2 standalone)
# ---------------------------------------------------------------------------

@router.post("/ocr", status_code=status.HTTP_200_OK)
async def ocr_report(
    user_id: str = Form(..., description="UUID of the report owner"),
    storage_path: str = Form(..., description="Supabase Storage path returned by /upload"),
):
    """Download a report from Storage, run OCR, and persist the result.

    Low-level endpoint. Use ``POST /reports/ingest`` for the full pipeline.
    """
    client = get_supabase_client()
    bucket = get_reports_bucket()
    table = get_ocr_reports_table()

    try:
        text, confidence, report_id = run_ocr_on_report(
            client=client,
            bucket=bucket,
            table=table,
            user_id=user_id,
            storage_path=storage_path,
        )
    except ReportOCRError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err

    return {
        "path": storage_path,
        "ocr_text": text,
        "confidence": confidence,
        "report_id": report_id,
    }


# ---------------------------------------------------------------------------
# POST /reports/extract-labs-gemini  — Gemini extraction for a saved report
# ---------------------------------------------------------------------------

@router.post("/extract-labs-gemini", status_code=status.HTTP_200_OK)
async def extract_labs_gemini(
    report_id: str = Form(..., description="UUID of a medical_reports row"),
):
    """Run Gemini AI extraction on stored OCR text and write to lab_results.

    The report must already have OCR text persisted (e.g. via ``/ocr``).
    The operation is idempotent — re-running deletes and re-inserts results.
    """
    client = get_supabase_client()

    try:
        result = extract_labs_with_gemini(client=client, report_id=report_id)
    except ReportOCRError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    except RuntimeError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err)
        ) from err

    return result


# ---------------------------------------------------------------------------
# POST /reports/ingest  — FULL ASYNC PIPELINE (recommended entry point)
# ---------------------------------------------------------------------------

@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_report(
    background_tasks: BackgroundTasks,
    user_id: str = Form(..., description="UUID of the report owner"),
    file: UploadFile = File(..., description="Medical report PDF or image"),
):
    """Upload a PDF/image and automatically run OCR + Gemini extraction.

    **Recommended endpoint** for the complete pipeline.

    The upload to Supabase Storage and the placeholder DB row are created
    synchronously, so the client receives a ``report_id`` immediately with
    HTTP 202.  OCR and Gemini extraction run as a background task *after*
    the response is sent.  Multiple concurrent requests each get an
    independent background job — processing happens in parallel across
    clients without blocking one another.

    Poll ``GET /reports/status/{report_id}`` to track progress.

    Pipeline stages (stored in ``medical_reports.processing_status``):
    - ``pending``      — uploaded, waiting for OCR
    - ``ocr_complete`` — OCR done, Gemini queued
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

    # Step 3 (async): OCR + Gemini run in background after response is sent.
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
    - ``ocr_confidence``: available once OCR completes
    - ``lab_results_count``: number of rows in ``lab_results`` (done only)
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
# POST /reports/process  — synchronous full pipeline (blocking, no polling)
# ---------------------------------------------------------------------------

@router.post("/process", status_code=status.HTTP_201_CREATED)
async def process_report(
    user_id: str = Form(..., description="UUID of the report owner"),
    file: UploadFile = File(..., description="Medical report PDF or image"),
):
    """Upload → OCR → Gemini extraction in one blocking call.

    Completes the full pipeline synchronously before returning.
    Convenient for scripts and testing; may be slow for large PDFs.
    For production use, prefer ``POST /reports/ingest`` (async).

    Gemini AI extraction is **always** used — there is no regex fallback.
    """
    file_bytes = await file.read()
    client = get_supabase_client()
    bucket = get_reports_bucket()
    table = get_ocr_reports_table()

    # Step 1: Upload to Supabase Storage.
    try:
        storage_path, public_url = upload_medical_report(
            client=client,
            bucket=bucket,
            user_id=user_id,
            original_filename=file.filename or "report.pdf",
            file_bytes=file_bytes,
            content_type=file.content_type or "application/pdf",
        )
    except ReportUploadError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err

    # Step 2: Run OCR and persist to medical_reports.
    try:
        ocr_text, confidence, report_id = run_ocr_on_report(
            client=client,
            bucket=bucket,
            table=table,
            user_id=user_id,
            storage_path=storage_path,
        )
    except ReportOCRError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err

    # Step 3: Gemini AI extraction (mandatory — no regex fallback).
    gemini_error: str | None = None
    gemini_result: dict = {}
    try:
        gemini_result = extract_labs_with_gemini(client=client, report_id=report_id)
    except Exception as err:  # noqa: BLE001
        gemini_error = str(err)

    return {
        "report_id": report_id,
        "storage_path": storage_path,
        "public_url": public_url,
        "processing_status": "done" if not gemini_error else "failed",
        "ocr_confidence": confidence,
        "ocr_text_preview": (ocr_text or "")[:500],
        "gemini_extraction": gemini_result,
        "gemini_error": gemini_error,
    }
