"""HTTP routes for report uploads."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend.config.supabase_client import (
    get_ocr_reports_table,
    get_reports_bucket,
    get_supabase_client,
)
from backend.controllers.reports_controller import (
    ReportOCRError,
    ReportUploadError,
    extract_labs_for_report,
    extract_labs_with_gemini,
    run_ocr_on_report,
    upload_medical_report,
)

router = APIRouter(prefix="/reports", tags=["reports"]) #Create api router with prefix


@router.post("/upload", status_code=status.HTTP_201_CREATED) #register route for report upload with POST method and 201 status code on success
async def upload_report(
    user_id: str = Form(..., description="Identifier for the report owner"),
    file: UploadFile = File(..., description="Medical report PDF or image"),
):
    """Upload a medical report to Supabase storage."""
    # Read the uploaded file into memory so it can be sent to Supabase Storage.
    file_bytes = await file.read()
    # Create a configured Supabase client and resolve the target bucket name.
    client = get_supabase_client()
    bucket = get_reports_bucket()

    try:
        # Delegate validation, path generation, and upload to the controller.
        storage_path, public_url = upload_medical_report(
            client=client,
            bucket=bucket,
            user_id=user_id,
            original_filename=file.filename or "report.pdf",
            file_bytes=file_bytes,
            content_type=file.content_type or "application/pdf",
        )
    except ReportUploadError as err:
        # Normalize upload failures into an HTTP 400 response.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err

    # Return the storage path and public URL for client access.
    return {"path": storage_path, "public_url": public_url}


@router.post("/ocr", status_code=status.HTTP_200_OK)
async def ocr_report(
    user_id: str = Form(..., description="Identifier for the report owner"),
    storage_path: str = Form(..., description="Supabase storage path of the report"),
):
    """Download a report from Supabase Storage, run OCR, and persist the result."""
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


@router.post("/extract-labs", status_code=status.HTTP_200_OK)
async def extract_labs(
    report_id: str = Form(..., description="UUID of the medical report"),
):
    """Extract lab results from OCR text using deterministic regex patterns and insert into lab_results.

    This is the **primary** extraction method — no API key required, works
    offline, fully deterministic.
    """
    client = get_supabase_client()

    try:
        inserted = extract_labs_for_report(client=client, report_id=report_id)
    except ReportOCRError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err

    return {
        "report_id": report_id,
        "inserted": inserted,
    }


@router.post("/extract-labs-gemini", status_code=status.HTTP_200_OK)
async def extract_labs_gemini(
    report_id: str = Form(..., description="UUID of the medical report"),
):
    """Extract lab results from OCR text using Gemini AI and insert into lab_results.

    This endpoint uses Google Gemini to intelligently extract structured lab
    data from the OCR text stored in medical_reports.  It handles OCR noise,
    varied report formats, and produces normalised results.

    The insertion is idempotent — calling this multiple times on the same
    report_id will delete and re-insert lab results each time.
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


@router.post("/process", status_code=status.HTTP_201_CREATED)
async def process_report(
    user_id: str = Form(..., description="Identifier for the report owner"),
    file: UploadFile = File(..., description="Medical report PDF or image"),
    use_gemini: bool = Form(False, description="Also run Gemini AI extraction (requires API key)"),
):
    """Full pipeline: upload → OCR → regex extraction (→ optional Gemini).

    Combines the upload, OCR, and deterministic regex extraction steps into
    a single endpoint.  If ``use_gemini=true`` is passed, Gemini AI extraction
    is attempted **in addition** to the regex path.

    Returns complete results including extraction counts.
    """
    file_bytes = await file.read()
    client = get_supabase_client()
    bucket = get_reports_bucket()
    table = get_ocr_reports_table()

    # Step 1: Upload to Supabase Storage
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

    # Step 2: Run OCR
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

    # Step 3: Deterministic regex extraction (primary — always runs)
    regex_inserted = 0
    regex_error = None
    try:
        regex_inserted = extract_labs_for_report(client=client, report_id=report_id)
    except Exception as err:
        regex_error = str(err)

    # Step 4 (optional): Gemini AI extraction
    gemini_result = {}
    gemini_error = None
    if use_gemini:
        try:
            gemini_result = extract_labs_with_gemini(client=client, report_id=report_id)
        except Exception as err:
            gemini_error = str(err)

    return {
        "report_id": report_id,
        "storage_path": storage_path,
        "public_url": public_url,
        "ocr_confidence": confidence,
        "ocr_text_preview": (ocr_text or "")[:500],
        "regex_extraction": {
            "inserted": regex_inserted,
            "error": regex_error,
        },
        "gemini_extraction": gemini_result if use_gemini else None,
        "gemini_error": gemini_error,
    }
