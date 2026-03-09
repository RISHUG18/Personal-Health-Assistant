"""Retrieval services — vector indexing, pgvector search, and FAISS fallback.

Public API
----------
``index_report``
    Clean + chunk + embed an OCR report and store it in Supabase ``report_chunks``.
``retrieve_context``
    Unified entry-point: dispatches to pgvector (default) or FAISS.
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

    Parameters
    ----------
    user_id:
        UUID of the user whose indexed chunks are searched.
    query:
        Natural-language query to match against stored chunks.
    top_k:
        Maximum number of chunks to return.
    match_threshold:
        Minimum cosine similarity (0\u20131) for a chunk to be included.    section_filter:
        # Week-4 Retrieval Optimization — optional section label filter.
        If provided, only chunks whose ``section_label`` matches are returned
        (e.g. ``"blood_test"``, ``"vitals"``).  ``None`` (default) returns all.    strategy:
        ``"pgvector"`` (default) \u2014 uses Supabase pgvector RPC; requires the
        ``pgvector`` extension and the ``match_report_chunks`` function to be
        deployed (see ``db/migrations/001_add_report_chunks.sql``).

        ``"faiss"`` \u2014 fetches embeddings from Supabase and searches locally
        using an in-memory FAISS index; no pgvector extension needed.

    Returns
    -------
    dict
        ``{"query_used": str, "retrieved_chunks": list[dict]}``
        Each chunk dict contains: ``chunk_id``, ``report_id``,
        ``chunk_index``, ``text_content``, ``relevance_score``, ``metadata``.
    """
    # Week-4 Retrieval Optimization — top-level timing
    t0 = time.perf_counter()

    if strategy == "faiss":
        chunks: List[Dict[str, Any]] = retrieve_faiss(
            user_id=user_id,
            query=query,
            top_k=top_k,
            match_threshold=match_threshold,
            section_filter=section_filter,
        )
    else:
        chunks = retrieve_pgvector(
            user_id=user_id,
            query=query,
            top_k=top_k,
            match_threshold=match_threshold,
            section_filter=section_filter,
        )

    total_ms = (time.perf_counter() - t0) * 1000

    # Week-4 Retrieval Optimization — summary log at dispatcher level
    logger.info(
        "retrieve_context: strategy=%s user_id=%s chunks=%d total_ms=%.1f "
        "section_filter=%s",
        strategy,
        user_id,
        len(chunks),
        total_ms,
        section_filter,
    )

    return {
        "query_used": query,
        "retrieved_chunks": chunks,
        # Week-4 Retrieval Optimization — timing metadata for callers
        "timing": {"total_ms": round(total_ms, 1)},
    }
