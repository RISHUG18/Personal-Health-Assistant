import base64
import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
import pytest # dummy
import os

try:
    import openai
except ImportError:
    openai = None

router = APIRouter(prefix="/voice", tags=["Voice"])
logger = logging.getLogger(__name__)

# NOTE: In a real production environment, you should initialize your OpenAI client securely
# using an API key from environment variables.
# client = openai.OpenAI()

async def transcribe_audio(file: UploadFile) -> str:
    """Transcribe audio using Whisper API."""
    try:
        # Dummy integration for now, in production you would use:
        # transcription = client.audio.transcriptions.create(
        #     model="whisper-1",
        #     file=(file.filename, file.file)
        # )
        # return transcription.text
        return "Dummy transcription from audio file."
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise HTTPException(status_code=500, detail="Error transcribing audio")

def generate_response(text: str) -> str:
    """Generate a dummy response or integrate with RAG in the future."""
    # Placeholder for week 5: DO NOT integrate RAG yet.
    return "I am processing your health data"

async def text_to_speech(text: str) -> bytes:
    """Convert text to speech using OpenAI TTS API."""
    try:
        # Dummy integration for now, in production you would use:
        # response = client.audio.speech.create(
        #     model="tts-1",
        #     voice="alloy",
        #     input=text
        # )
        # return response.content
        return b"dummy_audio_bytes"
    except Exception as e:
        logger.error(f"Error generating TTS: {e}")
        raise HTTPException(status_code=500, detail="Error generating TTS")

@router.post("/voice_chat")
async def voice_chat(
    text: Optional[str] = Form(None, description="Primary: The text transcript of the user's voice query."),
    file: Optional[UploadFile] = File(None, description="Fallback: The audio file of the user's voice query."),
    use_whisper: bool = Form(True, description="Flag to enable/disable whisper processing for audio files.")
):
    """
    Process a voice chat request.
    Supports either direct text input (primary) or an audio file (fallback).
    """
    if text:
        logger.info("[VOICE] Received request type: text")
        transcript = text
    elif file and use_whisper:
        logger.info("[VOICE] Received request type: audio")
        transcript = await transcribe_audio(file)
    elif file and not use_whisper:
        raise HTTPException(status_code=400, detail="Audio provided but use_whisper is False")
    else:
        raise HTTPException(status_code=400, detail="Either text or file must be provided")

    logger.info(f"[VOICE] Transcript: {transcript}")

    # Process text (dummy processing for now)
    response_text = generate_response(transcript)
    logger.info(f"[VOICE] Response: {response_text}")

    # Generate TTS
    audio_bytes = await text_to_speech(response_text)
    logger.info("[VOICE] TTS generated successfully")

    # Encode audio bytes to base64 to return in JSON
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    return JSONResponse(content={
        "transcript": transcript,
        "response_text": response_text,
        "audio_base64": audio_base64,
        "audio_format": "mp3"  # or wav, depending on the TTS provider
    })
