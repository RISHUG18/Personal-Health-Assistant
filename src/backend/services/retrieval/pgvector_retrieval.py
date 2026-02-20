"""Production top-k similarity retrieval via Supabase pgvector.

Calls the ``match_report_chunks`` PostgreSQL function (defined in
``db/migrations/001_add_report_chunks.sql``) through the Supabase PostgREST
RPC interface.

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
from typing import Any, Dict, List, Optional

from supabase import Client

from backend.config.supabase_client import get_supabase_client
from backend.services.embeddings.interfaces import Embedder
from backend.services.embeddings.query_embedding import embed_query as _embed_query

logger = logging.getLogger(__name__)

_MATCH_FN = "match_report_chunks"


def retrieve_pgvector(
    user_id: str,
    query: str,
    *,
    top_k: int = 5,
    match_threshold: float = 0.4,
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

    # ── Embed the query ───────────────────────────────────────────────────────
    vec = embedder.embed_query(query) if embedder is not None else _embed_query(query)

    db = client or get_supabase_client()

    # ── Call pgvector via RPC ─────────────────────────────────────────────────
    try:
        response = db.rpc(
            _MATCH_FN,
            {
                "query_embedding": vec,
                "match_user_id": user_id,
                "match_count": top_k,
                "match_threshold": match_threshold,
            },
        ).execute()
    except Exception as exc:
        raise RuntimeError(f"pgvector RPC call failed: {exc}") from exc

    rows: List[Dict[str, Any]] = response.data or []

    logger.info(
        "pgvector returned %d chunk(s) for user_id=%s query=%.50s",
        len(rows),
        user_id,
        query,
    )

    # ── Normalise to common result shape ─────────────────────────────────────
    return [
        {
            "chunk_id": row["id"],
            "report_id": row["report_id"],
            "chunk_index": row.get("chunk_index"),
            "text_content": row["chunk_text"],
            "relevance_score": round(float(row["similarity"]), 4),
            "metadata": {"source": "pgvector"},
        }
        for row in rows
    ]
