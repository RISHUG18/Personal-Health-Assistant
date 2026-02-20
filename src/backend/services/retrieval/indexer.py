"""Index a report's OCR text into the vector store.

Pipeline
--------
raw OCR text  →  clean  →  chunk  →  embed  →  upsert into ``report_chunks``

Calling :func:`index_report` after an OCR run ensures the report's text is
available for semantic (RAG) retrieval via :mod:`pgvector_retrieval` or
:mod:`faiss_retrieval`.

Usage::

    from backend.services.retrieval.indexer import index_report

    n = index_report(report_id="...", user_id="...", ocr_text=raw_text)
    print(f"Indexed {n} chunks")
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from supabase import Client

from backend.config.supabase_client import get_supabase_client
from backend.services.embeddings.interfaces import Embedder
from backend.services.embeddings.query_embedding import embed_texts
from backend.services.preprocessing.chunking import doc_to_chunks
from backend.services.preprocessing.text_cleaning import clean_full_text

logger = logging.getLogger(__name__)

_CHUNKS_TABLE = "report_chunks"


def index_report(
    report_id: str,
    user_id: str,
    ocr_text: str,
    *,
    client: Optional[Client] = None,
    embedder: Optional[Embedder] = None,
    chunk_size: int = 300,
    chunk_overlap: int = 50,
) -> int:
    """Clean, chunk, embed and persist an OCR report into the vector store.

    Parameters
    ----------
    report_id:
        UUID of the ``medical_reports`` row this text belongs to.
    user_id:
        UUID of the report owner (used for per-user retrieval scoping).
    ocr_text:
        Raw OCR text exactly as stored in ``medical_reports.ocr_text``.
    client:
        Optional pre-built Supabase client; defaults to the global singleton.
    embedder:
        Optional :class:`~backend.services.embeddings.interfaces.Embedder`
        implementation; defaults to the lazy global SentenceTransformer singleton.
    chunk_size:
        Target character count per chunk (passed to :func:`doc_to_chunks`).
    chunk_overlap:
        Character overlap between adjacent chunks.

    Returns
    -------
    int
        Number of chunks written to ``report_chunks``.

    Raises
    ------
    ValueError
        If any required argument is empty or not a valid UUID.
    RuntimeError
        If the Supabase upsert fails.
    """
    # ── Input validation ──────────────────────────────────────────────────────
    if not report_id:
        raise ValueError("report_id must not be empty.")
    if not user_id:
        raise ValueError("user_id must not be empty.")
    if not ocr_text or not ocr_text.strip():
        raise ValueError("ocr_text must not be empty.")

    try:
        uuid.UUID(report_id)
        uuid.UUID(user_id)
    except ValueError as exc:
        raise ValueError(
            f"report_id and user_id must be valid UUIDs: {exc}"
        ) from exc

    db = client or get_supabase_client()

    # ── 1. Clean ──────────────────────────────────────────────────────────────
    cleaned = clean_full_text(ocr_text)

    # ── 2. Chunk ──────────────────────────────────────────────────────────────
    chunks = doc_to_chunks(cleaned, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if not chunks:
        logger.warning(
            "No chunks produced for report_id=%s; skipping indexing.", report_id
        )
        return 0

    # ── 3. Embed ──────────────────────────────────────────────────────────────
    vectors = (
        embedder.embed_texts(chunks) if embedder is not None else embed_texts(chunks)
    )

    if len(vectors) != len(chunks):
        raise RuntimeError(
            f"Embedder returned {len(vectors)} vectors for {len(chunks)} chunks."
        )

    # ── 4. Upsert ─────────────────────────────────────────────────────────────
    rows = [
        {
            "id": str(uuid.uuid4()),
            "report_id": report_id,
            "user_id": user_id,
            "chunk_index": idx,
            "chunk_text": chunk,
            # PostgREST serialises Python lists to JSON arrays, which pgvector
            # accepts natively as vector literals.
            "embedding": vec,
        }
        for idx, (chunk, vec) in enumerate(zip(chunks, vectors))
    ]

    try:
        db.table(_CHUNKS_TABLE).upsert(rows, on_conflict="id").execute()
    except Exception as exc:
        raise RuntimeError(f"Failed to upsert report chunks: {exc}") from exc

    logger.info("Indexed %d chunks for report_id=%s", len(rows), report_id)
    return len(rows)
