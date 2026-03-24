"""FastAPI application entrypoint."""
from pathlib import Path

from dotenv import load_dotenv

# Load .env from src/backend/.env regardless of the working directory.
# This must run before any module that calls os.getenv() for Supabase/Gemini keys.
_ENV_FILE = Path(__file__).resolve().parent / ".env"
load_dotenv(_ENV_FILE, override=False)  # override=False: shell env vars win

from fastapi import FastAPI

from backend.routes import reports
from backend.routes import rag
from backend.routes import alerts
from backend.routes import users
from backend.routes import vitals
from backend.services.retrieval.mock_retrieval import retrieve_mock_context

app = FastAPI(
    title="Personal Health Assistant API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.get("/health")
def healthcheck() -> dict:
    return {"status": "ok"}

# Mount the reports router that exposes the Supabase upload endpoint.
app.include_router(reports.router)

# Production RAG query pipeline: retrieval → context assembly → (Gemini TBD).
app.include_router(rag.router)

# Alerts: fetch and evaluate deterministic health alerts per user.
app.include_router(alerts.router)

# Users: user management and profile operations.
app.include_router(users.router)

# Vitals: wearable device data ingestion and 7-day summary retrieval.
app.include_router(vitals.router)

# Temporary RAG test route for UI citation rendering.
@app.get("/api/v1/rag/test")
async def test_rag_retrieval(user_id: str, query: str) -> dict:
    return retrieve_mock_context(user_id, query)
