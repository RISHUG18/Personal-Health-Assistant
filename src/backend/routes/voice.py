import base64
import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Request
from fastapi.responses import JSONResponse
import pytest # dummy
import os
import logging
import base64

try:
    import openai
except ImportError:
    openai = None

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

def generate_response(text: str) -> str:
    """Generate a dummy response or integrate with RAG in the future."""
    return "I am processing your health data"

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

    if "application/json" in content_type:
        try:
            data = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")
        transcript = data.get("text")
        if not transcript:
            raise HTTPException(status_code=400, detail="Missing 'text' in JSON")
        logger.info("[VOICE] Received request type: text")

    elif "multipart/form-data" in content_type:
        if not USE_AUDIO:
            return JSONResponse(status_code=400, content={"error": "Audio disabled"})
        
        form = await request.form()
        file = form.get("file")
        if not file or not isinstance(file, UploadFile):
            raise HTTPException(status_code=400, detail="Missing 'file' in form data")
            
        logger.info("[VOICE] Received request type: audio")
        transcript = await transcribe_audio(file)
        
        if transcript == "Audio processing not available":
            return JSONResponse(status_code=400, content={"error": "Audio processing not available"})
    else:
        raise HTTPException(status_code=400, detail="Unsupported content type. Use application/json or multipart/form-data")

    if not transcript:
        raise HTTPException(status_code=400, detail="Either text or file must be provided")

    logger.info(f"[VOICE] Transcript: {transcript}")

    # Process text
    response_text = generate_response(transcript)
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
