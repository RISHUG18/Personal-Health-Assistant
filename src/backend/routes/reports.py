"""HTTP routes for report uploads."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from config.supabase_client import (
    get_ocr_reports_table,
    get_reports_bucket,
    get_supabase_client,
)
from controllers.reports_controller import (
    ReportOCRError,
    ReportUploadError,
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
        text, confidence = run_ocr_on_report(
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
    }
