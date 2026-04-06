"""Retrieval services — vector indexing, pgvector search, and FAISS fallback.

Public API
----------
``index_report``
    Clean + chunk + embed an OCR report and store it in Supabase ``report_chunks``.
``retrieve_context``
    Unified entry-point: dispatches to pgvector (default) or FAISS.
    When strategy is ``"pgvector"``, automatically falls back to FAISS on failure.
``retrieve_pgvector``
    Direct pgvector top-k search via Supabase RPC.
``retrieve_faiss``
    One-shot local FAISS search (offline / testing fallback).
``FaissRetriever``
    Reusable FAISS retriever class (avoid re-fetching on every query).
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional

from backend.services.retrieval.faiss_retrieval import FaissRetriever, retrieve_faiss
from backend.services.retrieval.indexer import index_report, reindex_report, find_stale_reports
from backend.services.retrieval.pgvector_retrieval import retrieve_pgvector

# Week-4 Retrieval Optimization — module-level logger
logger = logging.getLogger(__name__)

# Week-4 Retrieval Optimization — env-configurable defaults
_DEFAULT_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "10"))
_DEFAULT_MATCH_THRESHOLD = float(os.getenv("RETRIEVAL_MATCH_THRESHOLD", "0.4"))

__all__ = [
    "index_report",
    "reindex_report",
    "find_stale_reports",
    "retrieve_context",
    "retrieve_pgvector",
    "retrieve_faiss",
    "FaissRetriever",
]


def retrieve_context(
    user_id: str,
    query: str,
    *,
    top_k: int = _DEFAULT_TOP_K,
    match_threshold: float = _DEFAULT_MATCH_THRESHOLD,
    section_filter: Optional[str] = None,
    strategy: str = "pgvector",
) -> Dict[str, Any]:
    """Retrieve relevant report chunks for a user query.

    This is the primary entry-point for the RAG retrieval step.  It returns a
    dict in the same shape as the legacy mock, so callers do not need changes.

    Dispatch logic
    --------------
    **Path 1 — Explicit FAISS** (``strategy="faiss"``):
        Directly uses local in-memory FAISS search.  Use this for local
        development, integration tests, or when targeting databases that do not
        expose the ``pgvector`` extension (e.g. vanilla Postgres, SQLite stubs,
        or any Postgres host where the DB admin has not installed pgvector).
        Embeddings are fetched from Supabase and searched locally — no Postgres
        extension required on the DB side.

    **Path 2 — pgvector with automatic FAISS fallback** (``strategy="pgvector"``, default):
        Calls the ``match_report_chunks`` Supabase RPC for fast HNSW search.
        If pgvector is unavailable or the RPC raises for *any* reason
        (extension missing, function not deployed, network hiccup), the
        dispatcher **automatically retries using FAISS** so the pipeline
        degrades gracefully rather than surfacing a 500 to the user.
        The fallback is logged at ``WARNING`` level — visible in monitoring
        without triggering a high-severity alert on every request.

    **Path 3 — Both fail → graceful degradation**:
        If pgvector raises *and* FAISS also raises (e.g. Supabase is entirely
        offline so even the embedding fetch fails), both exceptions are caught,
        an ``ERROR`` is logged, and an empty ``retrieved_chunks`` list is
        returned.  The RAG pipeline then continues with zero chunk context so
        Gemini can still respond using structured data (lab results, alerts,
        wearable vitals) rather than crashing with a 500.

    Parameters
    ----------
    user_id:
        UUID of the user whose indexed chunks are searched.
    query:
        Natural-language query to match against stored chunks.
    top_k:
        Maximum number of chunks to return.
    match_threshold:
        Minimum cosine similarity (0–1) for a chunk to be included.
    section_filter:
        # Week-4 Retrieval Optimization — optional section label filter.
        If provided, only chunks whose ``section_label`` matches are returned
        (e.g. ``"blood_test"``, ``"vitals"``).  ``None`` (default) returns all.
    strategy:
        ``"pgvector"`` (default) — uses Supabase pgvector RPC; requires the
        ``pgvector`` extension and the ``match_report_chunks`` function to be
        deployed (see ``db/migrations/001_add_report_chunks.sql``).
        Automatically falls back to FAISS on any error.

        ``"faiss"`` — fetches embeddings from Supabase and searches locally
        using an in-memory FAISS index; no pgvector extension needed.

    Returns
    -------
    dict
        ``{"query_used": str, "retrieved_chunks": list[dict], "timing": dict}``
        Each chunk dict contains: ``chunk_id``, ``report_id``,
        ``chunk_index``, ``text_content``, ``relevance_score``, ``metadata``.
        ``timing`` includes ``total_ms`` and ``strategy_used`` (one of
        ``"pgvector"``, ``"faiss"``, ``"pgvector->faiss"``, ``"none"``).
    """
    # Week-4 Retrieval Optimization — top-level timing
    t0 = time.perf_counter()

    # ── Path 1: Explicit FAISS override ──────────────────────────────────────
    # Used for: local dev, tests, DBs without pgvector extension.
    if strategy == "faiss":
        chunks: List[Dict[str, Any]] = retrieve_faiss(
            user_id=user_id,
            query=query,
            top_k=top_k,
            match_threshold=match_threshold,
            section_filter=section_filter,
        )
        effective_strategy = "faiss"

    # ── Path 2: pgvector (production) with automatic FAISS fallback ──────────
    else:
        try:
            chunks = retrieve_pgvector(
                user_id=user_id,
                query=query,
                top_k=top_k,
                match_threshold=match_threshold,
                section_filter=section_filter,
            )
            effective_strategy = "pgvector"

        except Exception as pg_exc:
            logger.warning(
                "pgvector retrieval failed for user_id=%s — falling back to FAISS. "
                "Error: %s",
                user_id,
                pg_exc,
            )

            # ── Path 3: Both strategies fail → graceful degradation ────────
            try:
                chunks = retrieve_faiss(
                    user_id=user_id,
                    query=query,
                    top_k=top_k,
                    match_threshold=match_threshold,
                    section_filter=section_filter,
                )
                effective_strategy = "pgvector->faiss"

            except Exception as faiss_exc:
                logger.error(
                    "FAISS fallback also failed for user_id=%s — returning empty "
                    "chunk list so the pipeline can degrade gracefully. Error: %s",
                    user_id,
                    faiss_exc,
                )
                chunks = []
                effective_strategy = "none"

    total_ms = (time.perf_counter() - t0) * 1000

    # Week-4 Retrieval Optimization — summary log at dispatcher level
    logger.info(
        "retrieve_context: strategy=%s user_id=%s chunks=%d total_ms=%.1f "
        "section_filter=%s",
        effective_strategy,
        user_id,
        len(chunks),
        total_ms,
        section_filter,
    )

    return {
        "query_used": query,
        "retrieved_chunks": chunks,
        # Week-4 Retrieval Optimization — timing metadata for callers
        "timing": {
            "total_ms": round(total_ms, 1),
            # strategy_used reflects what actually ran: "pgvector", "faiss",
            # "pgvector->faiss" (automatic fallback), or "none" (both failed).
            "strategy_used": effective_strategy,
        },
    }
