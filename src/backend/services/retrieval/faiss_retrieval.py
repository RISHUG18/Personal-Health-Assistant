"""Local FAISS-based retrieval (offline / testing fallback).

Fetches chunk rows (including pre-computed embedding vectors) from Supabase,
builds an in-memory FAISS flat index, and performs exact cosine similarity
search locally — no pgvector extension required.

When to use
-----------
* The pgvector extension is unavailable.
* You need fully deterministic / reproducible search results for tests.
* Rapid local iteration without a live Supabase connection
  (swap ``client`` for a fixture/mock).

Limitations
-----------
* The FAISS index is **not persisted** between invocations.  For high query
  throughput, keep a :class:`FaissRetriever` instance alive across calls.
* All chunk embeddings for the user are loaded into RAM; avoid for users with
  tens of thousands of chunks in memory-constrained environments.

Usage::

    # One-shot convenience function
    from backend.services.retrieval.faiss_retrieval import retrieve_faiss

    results = retrieve_faiss(user_id="...", query="cholesterol levels")

    # Reusable instance (avoids re-fetching on every query)
    from backend.services.retrieval.faiss_retrieval import FaissRetriever

    searcher = FaissRetriever(user_id="...").build()
    results = searcher.search("HbA1c reading")
    more    = searcher.search("vitamin D deficiency")
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np
from supabase import Client

from backend.config.supabase_client import get_supabase_client
from backend.services.embeddings.interfaces import Embedder
from backend.services.embeddings.query_embedding import embed_query as _embed_query

logger = logging.getLogger(__name__)

_CHUNKS_TABLE = "report_chunks"


# ── Lazy faiss import ─────────────────────────────────────────────────────────

def _import_faiss():
    """Import faiss lazily so the module loads when faiss-cpu is absent."""
    try:
        import faiss  # noqa: PLC0415
        return faiss
    except ImportError as exc:
        raise ImportError(
            "faiss-cpu is required for local FAISS retrieval. "
            "Install it with:  pip install faiss-cpu"
        ) from exc


# ── Main class ────────────────────────────────────────────────────────────────

class FaissRetriever:
    """Builds an in-memory FAISS flat inner-product index from Supabase chunks.

    Because embeddings are L2-normalised (unit vectors), inner-product search
    is mathematically equivalent to cosine similarity search.

    Parameters
    ----------
    user_id:
        UUID of the user whose chunks will be loaded.
    client:
        Optional pre-built Supabase client; defaults to the global singleton.
    """

    def __init__(
        self,
        user_id: str,
        *,
        client: Optional[Client] = None,
    ) -> None:
        if not user_id:
            raise ValueError("user_id must not be empty.")
        self._user_id = user_id
        self._client = client or get_supabase_client()
        self._chunks: List[Dict[str, Any]] = []
        self._index = None           # set by build()
        self._dim: int = 0

    # ── Private helpers ───────────────────────────────────────────────────────

    def _fetch_chunks(self) -> List[Dict[str, Any]]:
        """Fetch all chunk rows including embeddings for this user.

        For chunks missing citation metadata (indexed before migration 002),
        a secondary lookup against ``medical_reports`` fills in
        ``source_filename`` and ``source_url`` — mirroring the ``COALESCE``
        fallback in the pgvector RPC.
        """
        try:
            response = (
                self._client.table(_CHUNKS_TABLE)
                .select(
                    "id, report_id, chunk_index, chunk_text, embedding, "
                    "source_filename, source_url, page_number"
                )
                .eq("user_id", self._user_id)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to fetch chunks from Supabase: {exc}"
            ) from exc

        rows = response.data or []

        # ── Backfill metadata for pre-migration chunks ────────────────────
        needs_backfill = [
            r for r in rows
            if not r.get("source_filename") and r.get("report_id")
        ]
        if needs_backfill:
            report_ids = list({r["report_id"] for r in needs_backfill})
            try:
                mr_resp = (
                    self._client.table("medical_reports")
                    .select("id, source_file_name, source_url")
                    .in_("id", report_ids)
                    .execute()
                )
                mr_map = {
                    mr["id"]: mr for mr in (mr_resp.data or [])
                }
            except Exception:
                mr_map = {}

            for r in needs_backfill:
                mr = mr_map.get(r["report_id"], {})
                if not r.get("source_filename"):
                    r["source_filename"] = mr.get("source_file_name")
                if not r.get("source_url"):
                    r["source_url"] = mr.get("source_url")

        return rows

    @staticmethod
    def _parse_embedding(raw: Any) -> List[float]:
        """Convert a pgvector value (list or bracketed string) to float list."""
        if isinstance(raw, list):
            return [float(x) for x in raw]
        if isinstance(raw, str):
            # PostgREST may return "[0.1, 0.2, ...]"
            return [float(x) for x in raw.strip("[]").split(",")]
        raise TypeError(f"Unexpected embedding type: {type(raw)}")

    def _build_index(self, chunks: List[Dict[str, Any]]):
        """Build a FAISS IndexFlatIP from the fetched chunk embeddings."""
        faiss = _import_faiss()

        embeddings: List[List[float]] = []
        valid_chunks: List[Dict[str, Any]] = []

        for row in chunks:
            raw = row.get("embedding")
            if raw is None:
                logger.debug("Skipping chunk %s — no embedding stored.", row.get("id"))
                continue
            try:
                vec = self._parse_embedding(raw)
            except (TypeError, ValueError) as exc:
                logger.warning("Skipping chunk %s — bad embedding: %s", row.get("id"), exc)
                continue
            embeddings.append(vec)
            valid_chunks.append(row)

        if not embeddings:
            return None, valid_chunks, 0

        matrix = np.array(embeddings, dtype=np.float32)
        dim = matrix.shape[1]
        index = faiss.IndexFlatIP(dim)  # exact search; inner product ~ cosine
        index.add(matrix)              # type: ignore[arg-type]
        return index, valid_chunks, dim

    # ── Public API ────────────────────────────────────────────────────────────

    def build(self) -> "FaissRetriever":
        """Fetch chunk embeddings from Supabase and construct the FAISS index.

        Must be called once before :meth:`search`.

        Returns
        -------
        FaissRetriever
            ``self``, for chaining: ``FaissRetriever(...).build().search(...)``.
        """
        raw_chunks = self._fetch_chunks()
        self._index, self._chunks, self._dim = self._build_index(raw_chunks)
        logger.info(
            "Built FAISS index: %d vectors (dim=%d) for user_id=%s",
            len(self._chunks),
            self._dim,
            self._user_id,
        )
        return self

    def search(
        self,
        query: str,
        *,
        top_k: int = 10,
        match_threshold: float = 0.4,
        embedder: Optional[Embedder] = None,
    ) -> List[Dict[str, Any]]:
        """Search the FAISS index for chunks most similar to *query*.

        Parameters
        ----------
        query:
            Natural-language query string.
        top_k:
            Maximum number of results.
        match_threshold:
            Minimum cosine similarity (0 – 1) to include a result.
        embedder:
            Optional embedder override; defaults to the lazy global singleton.

        Returns
        -------
        list of dict
            Each dict contains: ``chunk_id``, ``report_id``, ``chunk_index``,
            ``text_content``, ``relevance_score``, ``metadata``.

        Raises
        ------
        RuntimeError
            If :meth:`build` has not been called yet.
        """
        if self._index is None or not self._chunks:
            raise RuntimeError(
                "FAISS index is empty.  Call .build() before .search()."
            )

        # Embed the query
        vec = embedder.embed_query(query) if embedder is not None else _embed_query(query)
        q = np.array([vec], dtype=np.float32)

        k = min(top_k, len(self._chunks))
        scores, indices = self._index.search(q, k)  # type: ignore[arg-type]

        results: List[Dict[str, Any]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:           # FAISS pads with -1 when fewer than k results exist
                continue
            similarity = float(score)
            if similarity < match_threshold:
                continue
            row = self._chunks[int(idx)]
            results.append(
                {
                    "chunk_id": row["id"],
                    "report_id": row["report_id"],
                    "chunk_index": row.get("chunk_index"),
                    "text_content": row["chunk_text"],
                    "relevance_score": round(similarity, 4),
                    "metadata": {
                        "source_filename": row.get("source_filename"),
                        "source_url": row.get("source_url"),
                        "page_number": row.get("page_number"),
                        "source": "faiss",
                    },
                }
            )

        logger.info(
            "FAISS returned %d chunk(s) for user_id=%s query=%.50s",
            len(results),
            self._user_id,
            query,
        )
        return results


# ── Convenience function ──────────────────────────────────────────────────────

def retrieve_faiss(
    user_id: str,
    query: str,
    *,
    top_k: int = 10,
    match_threshold: float = 0.4,
    client: Optional[Client] = None,
    embedder: Optional[Embedder] = None,
) -> List[Dict[str, Any]]:
    """One-shot FAISS retrieval: build index then search.

    For repeated queries over the same user, prefer constructing and reusing a
    :class:`FaissRetriever` instance to avoid re-fetching on every call.

    Parameters
    ----------
    user_id:
        UUID of the user whose chunks are searched.
    query:
        Natural-language query string.
    top_k:
        Maximum number of results.
    match_threshold:
        Minimum cosine similarity to include a result.
    client:
        Optional pre-built Supabase client.
    embedder:
        Optional embedder override.

    Returns
    -------
    list of dict
        Same shape as :func:`~pgvector_retrieval.retrieve_pgvector` output.
    """
    retriever = FaissRetriever(user_id=user_id, client=client).build()
    return retriever.search(
        query,
        top_k=top_k,
        match_threshold=match_threshold,
        embedder=embedder,
    )
