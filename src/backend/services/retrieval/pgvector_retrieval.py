"""Production top-k similarity retrieval via Supabase pgvector.

Calls the ``match_report_chunks`` PostgreSQL function (defined and last
updated in ``db/migrations/002_add_report_chunk_metadata.sql``) through
the Supabase PostgREST RPC interface.

Requirements
------------
- The ``pgvector`` extension must be enabled in the Supabase project.
- The ``match_report_chunks`` function must be deployed.
- Report chunks must have been previously indexed via
  :func:`~backend.services.retrieval.indexer.index_report`.

Usage::

    from backend.services.retrieval.pgvector_retrieval import retrieve_pgvector

    results = retrieve_pgvector(user_id="...", query="blood sugar levels")
    for r in results:
        print(r["relevance_score"], r["text_content"])
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional

from supabase import Client

from backend.config.supabase_client import get_supabase_client
from backend.services.embeddings.interfaces import Embedder
from backend.services.embeddings.query_embedding import embed_query as _embed_query

logger = logging.getLogger(__name__)

_MATCH_FN = "match_report_chunks"

# Week-4 Retrieval Optimization — env-configurable defaults
_DEFAULT_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "10"))
_DEFAULT_MATCH_THRESHOLD = float(os.getenv("RETRIEVAL_MATCH_THRESHOLD", "0.4"))


def retrieve_pgvector(
    user_id: str,
    query: str,
    *,
    top_k: int = _DEFAULT_TOP_K,
    match_threshold: float = _DEFAULT_MATCH_THRESHOLD,
    section_filter: Optional[str] = None,
    client: Optional[Client] = None,
    embedder: Optional[Embedder] = None,
) -> List[Dict[str, Any]]:
    """Return the top-k most semantically similar chunks for *query*.

    The query is embedded with the configured
    :class:`~backend.services.embeddings.interfaces.Embedder` and then passed
    to the ``match_report_chunks`` Supabase RPC function, which performs an
    HNSW approximate nearest-neighbour search over the stored pgvector index.

    Parameters
    ----------
    user_id:
        UUID of the user whose chunks are searched.
    query:
        Natural-language query string (e.g. ``"HbA1c levels"``).
    top_k:
        Maximum number of chunks to return.
    match_threshold:
        Minimum cosine similarity (0 – 1) for a chunk to be included.
        Increase this for higher-precision but lower-recall retrieval.
    section_filter:
        # Week-4 Retrieval Optimization — optional section label filter.
        If provided, only chunks matching this section_label are returned
        (e.g. ``"blood_test"``, ``"vitals"``).
    client:
        Optional pre-built Supabase client; defaults to the global singleton.
    embedder:
        Optional embedder override; defaults to the lazy global singleton.

    Returns
    -------
    list of dict
        Each dict contains:
        ``chunk_id``, ``report_id``, ``chunk_index``,
        ``text_content``, ``relevance_score``, ``metadata``.

    Raises
    ------
    ValueError
        If *user_id* or *query* is empty.
    RuntimeError
        If the Supabase RPC call fails.
    """
    if not user_id or not query:
        raise ValueError("user_id and query must be non-empty.")

    # ── Week-4 Retrieval Optimization — latency instrumentation ───────────────
    t0 = time.perf_counter()

    # ── Embed the query ───────────────────────────────────────────────────────
    vec = embedder.embed_query(query) if embedder is not None else _embed_query(query)

    t_embed = time.perf_counter()
    embed_ms = (t_embed - t0) * 1000

    db = client or get_supabase_client()

    # ── Call pgvector via RPC ─────────────────────────────────────────────────
    # Week-4 Retrieval Optimization — pass optional section_filter to RPC
    rpc_params: Dict[str, Any] = {
        "query_embedding": vec,
        "match_user_id": user_id,
        "match_count": top_k,
        "match_threshold": match_threshold,
    }
    if section_filter:
        rpc_params["filter_section_label"] = section_filter

    try:
        response = db.rpc(_MATCH_FN, rpc_params).execute()
    except Exception as exc:
        raise RuntimeError(f"pgvector RPC call failed: {exc}") from exc

    t_search = time.perf_counter()
    search_ms = (t_search - t_embed) * 1000
    total_ms = (t_search - t0) * 1000

    rows: List[Dict[str, Any]] = response.data or []

    # ── Week-4 Retrieval Optimization — structured retrieval log ──────────────
    logger.info(
        "pgvector retrieval: user_id=%s chunks=%d embed_ms=%.1f search_ms=%.1f total_ms=%.1f "
        "top_k=%d threshold=%.2f section_filter=%s query=%.60s",
        user_id,
        len(rows),
        embed_ms,
        search_ms,
        total_ms,
        top_k,
        match_threshold,
        section_filter,
        query,
    )

    # ── Normalise to common result shape ─────────────────────────────────────
    # Week-3 RAG ingestion improvement — include section_label, report_date,
    # embedding_version in metadata for downstream consumers.
    return [
        {
            "chunk_id": row["id"],
            "report_id": row["report_id"],
            "chunk_index": row.get("chunk_index"),
            "text_content": row["chunk_text"],
            "relevance_score": round(float(row["similarity"]), 4),
            "metadata": {
                "source_filename": row.get("source_filename"),
                "source_url": row.get("source_url"),
                "page_number": row.get("page_number"),
                "source": "pgvector",
                # Week-3 RAG ingestion improvement — new metadata fields
                "section_label": row.get("section_label", "other"),
                "report_date": row.get("report_date"),
                "embedding_version": row.get("embedding_version"),
            },
        }
        for row in rows
    ]
