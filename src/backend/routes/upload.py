"""Upload endpoints with Auth integration for structured medical reports."""
import logging
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from backend.config.supabase_client import get_supabase_client, get_reports_bucket
from backend.middleware.auth_middleware import get_current_user

_log = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/report", status_code=status.HTTP_201_CREATED)
async def upload_structured_report(
    file: UploadFile = File(..., description="PDF medical report"),
    user_id: str = Depends(get_current_user)
):
    """Protected endpoint to validate, upload, and track a medical report PDF."""
    
    # 1. Validate PDF file type
    if file.content_type != "application/pdf" and not (file.filename and file.filename.lower().endswith('.pdf')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Unauthorized upload type: Only PDF files are allowed"
        )
        
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Unauthorized upload: File is empty"
        )
        
    client = get_supabase_client()
    bucket = get_reports_bucket()
    
    # 3. Generate a stable report UUID
    report_id = str(uuid.uuid4())
    
    # 2. Upload to storage bucket directly
    try:
        # Standardize storage_path 
        storage_path = f"{user_id}/{report_id}_{file.filename or 'report.pdf'}"
        
        # Upload using supabase storage API
        client.storage.from_(bucket).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": file.content_type or "application/pdf"}
        )
        
        # Get public url. Supabase Python client get_public_url requires simple path.
        public_url = client.storage.from_(bucket).get_public_url(storage_path)
        
    except Exception as exc:
        _log.error("Storage upload failed for user %s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Storage failure: Could not save file."
        ) from exc

    # 4. Insert metadata into structured_reports table
    struct_id = str(uuid.uuid4())
    try:
        client.table("structured_reports").insert({
            "id": struct_id,
            "user_id": user_id,
            "report_id": report_id,
            "file_url": public_url,
            "extracted_data": {} # JSONB default empty
        }).execute()
        _log.info("Inserted %s into structured_reports for user %s.", struct_id, user_id)
    except Exception as exc:
        _log.error("DB insertion failed into structured_reports for user %s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="DB failure: Could not create structured record."
        ) from exc
        
    return {
        "message": "Report uploaded successfully",
        "structured_report_id": struct_id,
        "report_id": report_id,
        "file_url": public_url
    }
