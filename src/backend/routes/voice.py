import base64
import logging
import os
import uuid

from fastapi import APIRouter, HTTPException, UploadFile, Request
from fastapi.responses import JSONResponse


def is_valid_uuid(val: str) -> bool:
    try:
        if not val:
            return False
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

try:
    import openai
except ImportError:
    openai = None

from backend.routes.rag import rag_query, RagQueryRequest

router = APIRouter(prefix="/voice", tags=["Voice"])
logger = logging.getLogger(__name__)

# Temporary flag to disable audio processing fully
USE_AUDIO = os.getenv("USE_AUDIO", "false").lower() == "true"

async def transcribe_audio(file: UploadFile) -> str:
    """Transcribe audio using Whisper API."""
    if not USE_AUDIO or not openai:
        return "Audio processing not available"
    try:
        # Dummy integration for now
        return "Dummy transcription from audio file."
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise HTTPException(status_code=500, detail="Error transcribing audio")

async def generate_response(
    text: str,
    target_user_id: str,
    current_user: dict,
    role: str = "user",
    user_lat: float | None = None,
    user_lon: float | None = None,
    user_location: str | None = None,
    use_rag: bool = True
) -> str:
    """Generate a response by calling the real RAG + Gemini pipeline."""
    if not use_rag:
        return "I am processing your health data (RAG disabled)"
        
    logger.info("[VOICE] Calling RAG")
    try:
        req = RagQueryRequest(
            user_id=target_user_id,
            query=text,
            role=role,
            user_lat=user_lat,
            user_lon=user_lon,
            user_location=user_location,
            retrieval_strategy="pgvector",
            top_k=5, # lighter context for voice
            match_threshold=0.4
        )
        
        # Call the underlying RAG logic directly with an authenticated context
        # object equivalent to get_current_user_with_role's return shape.
        res = await rag_query(body=req, current_user=current_user)
        
        answer = res.get("answer", "")
        chunks_retrieved = res.get("chunks_retrieved", 0)
        
        logger.info(
            "[RAG] requester_id=%s requester_role=%s target_user_id=%s rag_role=%s",
            current_user.get("id"),
            current_user.get("role"),
            target_user_id,
            role,
        )
        logger.info(f"[RETRIEVAL] chunks retrieved: {chunks_retrieved}")
        
        if chunks_retrieved == 0:
            logger.warning(f"[WARNING] No chunks found for user_id={target_user_id}")
        
        if not answer:
            return "I'm having trouble accessing your health data right now."
            
        if chunks_retrieved == 0 and res.get("grounding_available") is False:
            return answer # The LLM will already say it doesn't have records grounded, so we just return the safe generic LLM answer
            
        logger.info("[VOICE] RAG response received successfully")
        return answer
    except Exception as e:
        logger.error(f"[VOICE] RAG failed: {e}")
        return "I'm having trouble accessing your health data right now."

async def text_to_speech(text: str) -> bytes:
    """Convert text to speech using OpenAI TTS API."""
    try:
        return b"dummy_audio_bytes"
    except Exception as e:
        logger.error(f"Error generating TTS: {e}")
        raise HTTPException(status_code=500, detail="Error generating TTS")

@router.post("/voice_chat")
async def voice_chat(request: Request):
    """
    Process a voice chat request.
    Supports either direct text input (application/json) or an audio file (multipart/form-data).
    """
    content_type = request.headers.get("content-type", "")
    transcript = None
    requested_user_id = None
    requested_role = None
    user_lat, user_lon = None, None
    user_location = None
    use_rag = True

    if "application/json" in content_type:
        try:
            data = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")
        transcript = data.get("text")
        if not transcript:
            raise HTTPException(status_code=400, detail="Missing 'text' in JSON")
        
        requested_user_id = data.get("user_id", data.get("userId"))
        requested_role = data.get("role")
        user_lat = data.get("user_lat")
        user_lon = data.get("user_lon")
        user_location = data.get("user_location")
        use_rag = data.get("use_rag", True)
        
        logger.info("[VOICE] Received request type: text")

    elif "multipart/form-data" in content_type:
        if not USE_AUDIO:
            return JSONResponse(status_code=400, content={"error": "Audio disabled"})
        
        form = await request.form()
        file = form.get("file")
        if not file or not isinstance(file, UploadFile):
            raise HTTPException(status_code=400, detail="Missing 'file' in form data")
            
        requested_user_id = form.get("user_id", form.get("userId"))
        requested_role = form.get("role")
        lat_val = form.get("user_lat")
        lon_val = form.get("user_lon")
        if lat_val and str(lat_val).strip(): user_lat = float(lat_val)
        if lon_val and str(lon_val).strip(): user_lon = float(lon_val)
        user_location = form.get("user_location")
        use_rag = str(form.get("use_rag", "true")).lower() == "true"
            
        logger.info("[VOICE] Received request type: audio")
        transcript = await transcribe_audio(file)
        
        if transcript == "Audio processing not available":
            return JSONResponse(status_code=400, content={"error": "Audio processing not available"})
    else:
        raise HTTPException(status_code=400, detail="Unsupported content type. Use application/json or multipart/form-data")

    if not transcript:
        raise HTTPException(status_code=400, detail="Either text or file must be provided")

    logger.info(f"[VOICE] Transcript: {transcript}")

    # 1. Try to extract from Authorization header
    auth_header = request.headers.get("Authorization")
    logger.info(f"[VOICE DEBUG] Authorization header: {auth_header}")
    
    auth_user = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            from backend.config.supabase_client import get_supabase_client
            client = get_supabase_client()
            user_resp = client.auth.get_user(token)
            if user_resp and user_resp.user:
                auth_user_id = user_resp.user.id
                role_resp = (
                    client.table("users")
                    .select("role")
                    .eq("id", auth_user_id)
                    .limit(1)
                    .execute()
                )
                role_rows = role_resp.data or []
                resolved_role = (
                    role_rows[0].get("role") if role_rows else "patient"
                ) or "patient"
                auth_user = {
                    "id": auth_user_id,
                    "role": str(resolved_role).lower(),
                }
        except Exception as e:
            logger.warning(f"Auth token validation failed in voice_chat: {e}")
            
    # 2. Resolve target user id. If auth exists and caller passed user_id,
    # treat it as an explicit target (doctor -> patient). Otherwise default
    # to authenticated user id.
    resolved_user_id = requested_user_id or (auth_user.get("id") if auth_user else None)

    logger.info(
        "[VOICE DEBUG] requested_user_id=%s auth_user=%s",
        requested_user_id,
        auth_user.get("id") if auth_user else None,
    )

    if not resolved_user_id:
        raise HTTPException(
            status_code=401,
            detail="Missing user_id"
        )

    if not is_valid_uuid(resolved_user_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid user_id format"
        )

    # Backward-compatible unauthenticated mode: treat caller as the same user.
    current_user = auth_user or {"id": resolved_user_id, "role": "patient"}

    # role controls the prompt style inside rag_query; if absent, infer from
    # authenticated caller role.
    resolved_query_role = str(requested_role or "").strip().lower()
    if resolved_query_role not in {"user", "doctor"}:
        resolved_query_role = "doctor" if current_user.get("role") == "doctor" else "user"
        
    logger.info(
        "[VOICE] requester_id=%s requester_role=%s target_user_id=%s rag_role=%s",
        current_user.get("id"),
        current_user.get("role"),
        resolved_user_id,
        resolved_query_role,
    )

    # Process text through RAG
    response_text = await generate_response(
        text=transcript,
        target_user_id=resolved_user_id,
        current_user=current_user,
        role=resolved_query_role,
        user_lat=user_lat,
        user_lon=user_lon,
        user_location=user_location,
        use_rag=use_rag
    )
    logger.info(f"[VOICE] Response: {response_text}")

    # Generate TTS
    audio_bytes = await text_to_speech(response_text)
    logger.info("[VOICE] TTS generated successfully")

    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    return JSONResponse(content={
        "transcript": transcript,
        "response_text": response_text,
        "audio_base64": audio_base64,
        "audio_format": "mp3"
    })
