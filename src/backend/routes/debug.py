from fastapi import APIRouter, HTTPException
from backend.config.supabase_client import get_supabase_client

router = APIRouter(prefix="/debug", tags=["Debug"])

@router.get("/user_data/{email}")
async def get_user_data(email: str):
    client = get_supabase_client()
    user_resp = client.table("users").select("*").eq("email", email).execute()
    
    if not user_resp.data:
        raise HTTPException(status_code=404, detail="User not found in public.users")
    
    user = user_resp.data[0]
    user_id = user["id"]
    
    result = {"user_id": user_id, "email": email, "counts": {}}
    
    # Reports
    try:
        reports_resp = client.table("medical_reports").select("id").eq("user_id", user_id).execute()
        result["counts"]["medical_reports"] = len(reports_resp.data)
        result["reports"] = client.table("medical_reports").select("id, report_date").eq("user_id", user_id).execute().data
    except Exception as e:
        result["counts"]["medical_reports_error"] = str(e)
        
    # Lab results
    try:
        # We can fetch how many reports actually have lab results
        report_ids = [r["id"] for r in result.get("reports", [])]
        if report_ids:
            labs_resp = client.table("lab_results").select("id", count="exact").in_("report_id", report_ids).execute()
            result["counts"]["lab_results"] = labs_resp.count
        else:
            result["counts"]["lab_results"] = 0
    except Exception as e:
        pass
        
    # Chunks
    try:
        chunks_resp = client.table("report_chunks").select("id", count="exact").eq("user_id", user_id).execute()
        result["counts"]["report_chunks"] = chunks_resp.count
    except Exception as e:
        result["counts"]["report_chunks_error"] = str(e)
        
    return result
