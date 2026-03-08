"""HTTP routes for the AI query pipeline.

POST /api/v1/rag_query
    Full pipeline: retrieval → data fetching → context assembly.
    Returns a structured context payload ready for the Gemini prompt layer.
    (Gemini integration is wired here once that service is implemented.)
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.config.supabase_client import get_supabase_client
from backend.services.context.context_builder import build_context
from backend.services.context.data_fetchers import (
    fetch_active_alerts,
    fetch_user_lab_snapshot,
    fetch_user_profile,
)
from backend.services.retrieval import retrieve_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["rag"])


# ── Request / Response models ─────────────────────────────────────────────────

#This model defines the expected structure of the request body for the RAG query endpoint. 
#It includes fields for user ID, query, role, retrieval strategy, and optional environment and wearable data. 
#The response from the endpoint will include the assembled context, number of chunks retrieved, and a note about the pipeline stage reached.
class RagQueryRequest(BaseModel):
    user_id: str = Field(..., description="UUID of the user asking the question")
    query: str = Field(..., description="Natural-language question")
    role: str = Field(
        "user",
        description="'user' (wellbeing coach) or 'doctor' (clinical assistant)",
    )
    retrieval_strategy: str = Field(
        "pgvector",
        description="'pgvector' (default) or 'faiss' (local fallback)",
    )
    top_k: int = Field(10, ge=1, le=10, description="Max chunks to retrieve")
    match_threshold: float = Field(
        0.4, ge=0.0, le=1.0, description="Minimum cosine similarity"
    )
    # Optional environment block — callers may pass live AQI/weather data.
    environment: Optional[dict] = Field(
        None,
        description=(
            "Environmental context e.g. "
            '{"aqi_level": 85, "weather_condition": "Sunny", "location_city": "Delhi"}'
        ),
    )
    # Optional wearable block — callers may pass synced wearable data.
    wearable_data: Optional[dict] = Field(
        None,
        description="Wearable device snapshot (steps, sleep, HR, etc.)",
    )


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post("/rag_query", status_code=status.HTTP_200_OK)
async def rag_query(body: RagQueryRequest) -> dict:
    """Run the full RAG + context-assembly pipeline for one user query.

    Pipeline
    --------
    1. **Retrieval** — embed the query and find the top-k most similar report
       chunks from the user's indexed medical reports.
    2. **Data fetching** — pull structured lab results, recent vitals, and
       active alerts from Supabase (each fetch is best-effort; failures fall
       back to empty dicts/lists so the pipeline never hard-fails due to a
       missing data source).
    3. **Context assembly** — :func:`build_context` validates all inputs and
       produces a single, well-typed :class:`BuiltContext` object.
    4. **Return** — the serialised context is returned as ``context`` in the
       response body.  When the Gemini prompt layer is implemented, this
       function will additionally call it and return the LLM answer.

    Returns
    -------
    JSON object with keys:

    ``context``
        The fully assembled context object (see ``BuiltContext`` model).
    ``chunks_retrieved``
        Number of RAG chunks that passed the similarity threshold.
    ``note``
        Human-readable message indicating the pipeline stage reached.
    """
    if not body.user_id or not body.query:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="user_id and query must not be empty.",
        )

    client = get_supabase_client()

    # ── Step 1: Vector retrieval ──────────────────────────────────────────────
    try:
        retrieval_result = retrieve_context(
            user_id=body.user_id,
            query=body.query,
            top_k=body.top_k,
            match_threshold=body.match_threshold,
            strategy=body.retrieval_strategy,
        )
        retrieved_chunks = retrieval_result.get("retrieved_chunks", [])
    except Exception as exc:  # noqa: BLE001
        logger.error("Retrieval failed for user_id=%s: %s", body.user_id, exc)
        # Retrieval failure is non-fatal: context builder handles empty chunks.
        retrieved_chunks = []

    # ── Step 2: Structured data fetching (all best-effort) ────────────────────
    alerts = fetch_active_alerts(user_id=body.user_id, client=client)
    medical_snapshot = fetch_user_lab_snapshot(user_id=body.user_id, client=client)
    user_profile = fetch_user_profile(user_id=body.user_id, client=client)

    # ── Step 3: Context assembly ──────────────────────────────────────────────
    try:
        context = build_context(
            query=body.query,
            user_id=body.user_id,
            retrieved_chunks=retrieved_chunks,
            user_profile=user_profile,
            medical_snapshot=medical_snapshot,
            alerts=alerts,
            environment=body.environment,
            wearable_data=body.wearable_data,
            role=body.role,
        )
    except Exception as exc:
        logger.exception("Context assembly failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Context assembly error: {exc}",
        ) from exc

    # ── Step 4: (Future) call Gemini with context ─────────────────────────────
    # TODO: replace note with actual LLM response once Gemini service is wired.

    return {
        "context": context.model_dump(),
        "chunks_retrieved": len(context.rag_knowledge_base.retrieved_chunks),
        "note": (
            "Context assembled successfully. "
            "Gemini integration pending — context is ready to pass to the prompt layer."
        ),
    }
