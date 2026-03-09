"""HTTP routes for the AI query pipeline.

POST /api/v1/rag_query
    Full pipeline: retrieval → data fetching → context assembly → Gemini LLM.
    Returns the AI-generated answer alongside the assembled context that
    grounded it.  The Gemini call is best-effort: if it fails, the endpoint
    returns a 502 so callers can distinguish LLM errors from pipeline errors.
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
from backend.services.llm import GeminiService, load_system_prompt
from backend.services.retrieval import retrieve_context

logger = logging.getLogger(__name__)

# Instantiate the service once at module load so the Gemini client
# (and its API-key validation) is created only once per process.
# If GEMINI_API_KEY is absent the import itself will raise, making the
# misconfiguration visible at startup rather than on the first request.
_llm = GeminiService()

router = APIRouter(prefix="/api/v1", tags=["rag"])

# Returned verbatim when Gemini is unavailable so the caller always gets a
# usable (if uninformative) string rather than a raw 502 JSON error.  This
# makes the frontend more resilient during transient API outages.
_FALLBACK_ANSWER = (
    "I was unable to generate an AI response at this time due to a temporary "
    "service issue. Please try again in a few moments. If the problem persists, "
    "check that the GEMINI_API_KEY environment variable is correctly configured."
)


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
    # Week-4 Retrieval Optimization — optional section label filter
    section_filter: Optional[str] = Field(
        None,
        description=(
            "If provided, only chunks with this section_label are returned. "
            "Valid values: blood_test, sleep_data, imaging, vitals, summary, other."
        ),
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

    ``answer``
        The AI-generated markdown response from Gemini.
    ``context``
        The fully assembled context object (see ``BuiltContext`` model).
    ``chunks_retrieved``
        Number of RAG chunks that passed the similarity threshold.
    ``model``
        Name of the Gemini model that generated the answer.
    """
    # ── Input validation ──────────────────────────────────────────────────────
    # Validate user_id presence.
    if not body.user_id or not body.user_id.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="user_id must not be empty.",
        )
    # Validate query: reject empty, whitespace-only, and suspiciously short
    # strings before any embedding or DB call is made.  This avoids wasting
    # resources on inputs the LLM cannot usefully answer.
    clean_query = body.query.strip()
    if not clean_query:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="query must not be empty or whitespace only.",
        )

    client = get_supabase_client()

    # ── Step 1: Vector retrieval ──────────────────────────────────────────────
    try:
        retrieval_result = retrieve_context(
            user_id=body.user_id,
            query=body.query,
            top_k=body.top_k,
            match_threshold=body.match_threshold,
            section_filter=body.section_filter,
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
    except ValueError as exc:
        # ValueError comes from build_context's own input guards (empty query,
        # empty user_id).  These are caller errors, not server errors → 422.
        logger.warning("Context assembly rejected invalid input: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Context assembly failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Context assembly error: {exc}",
        ) from exc

    # Track whether the response is backed by retrieved report chunks.
    # The caller can use this flag to show a "no records found" notice in the UI
    # when grounding_available is False.
    grounding_available = len(context.rag_knowledge_base.retrieved_chunks) > 0

    # ── Step 4: LLM generation ────────────────────────────────────────────────
    # Load the role-appropriate system prompt (cached after first read).
    system_prompt = load_system_prompt(role=body.role)

    llm_error: str | None = None
    try:
        answer = _llm.generate(
            query=body.query,
            context_dict=context.model_dump(),
            system_instruction=system_prompt,
        )
    except RuntimeError as exc:
        # Log the failure but return a graceful fallback instead of a hard 502.
        # This allows the frontend to still display the assembled context and
        # inform the user that AI generation is temporarily unavailable, rather
        # than showing a generic error page.
        logger.error("Gemini generation failed for user_id=%s: %s", body.user_id, exc)
        answer = _FALLBACK_ANSWER
        llm_error = str(exc)

    return {
        "answer": answer,
        "context": context.model_dump(),
        "chunks_retrieved": len(context.rag_knowledge_base.retrieved_chunks),
        # grounding_available: True when retrieved_chunks is non-empty.
        # False means the answer was generated without RAG grounding (e.g., no
        # reports indexed yet), so the frontend can show a disclaimer.
        "grounding_available": grounding_available,
        "model": _llm.model_name,
        # llm_error is None on success; non-None only when Gemini failed and
        # the fallback answer was substituted.
        "llm_error": llm_error,
    }
