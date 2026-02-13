"""FastAPI application entrypoint."""
from fastapi import FastAPI

from backend.routes import reports
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

# Temporary RAG test route for UI citation rendering.
@app.get("/api/v1/rag/test")
async def test_rag_retrieval(user_id: str, query: str) -> dict:
    return retrieve_mock_context(user_id, query)
