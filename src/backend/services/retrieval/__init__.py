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

from typing import Any, Dict, List, Optional

from backend.services.retrieval.faiss_retrieval import FaissRetriever, retrieve_faiss
from backend.services.retrieval.indexer import index_report
from backend.services.retrieval.pgvector_retrieval import retrieve_pgvector

__all__ = [
    "index_report",
    "retrieve_context",
    "retrieve_pgvector",
    "retrieve_faiss",
    "FaissRetriever",
]


def retrieve_context(
    user_id: str,
    query: str,
    *,
    top_k: int = 5,
    match_threshold: float = 0.4,
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
        Minimum cosine similarity (0\u20131) for a chunk to be included.
    strategy:
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
    if strategy == "faiss":
        chunks: List[Dict[str, Any]] = retrieve_faiss(
            user_id=user_id,
            query=query,
            top_k=top_k,
            match_threshold=match_threshold,
        )
    else:
        chunks = retrieve_pgvector(
            user_id=user_id,
            query=query,
            top_k=top_k,
            match_threshold=match_threshold,
        )

    return {
        "query_used": query,
        "retrieved_chunks": chunks,
    }
