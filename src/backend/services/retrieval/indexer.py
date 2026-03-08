"""Index a report's OCR text into the vector store.

Pipeline
--------
raw OCR text  →  clean  →  chunk  →  embed  →  upsert into ``report_chunks``

Calling :func:`index_report` after an OCR run ensures the report's text is
available for semantic (RAG) retrieval via :mod:`pgvector_retrieval` or
:mod:`faiss_retrieval`.

# Week-3 RAG ingestion improvement
# - Uses doc_to_chunks_with_metadata for section-label-aware chunking
# - Stores section_label, report_date, embedding_version per chunk
# - Supports re-embedding via embedding_version tracking

Usage::

    from backend.services.retrieval.indexer import index_report

    n = index_report(report_id="...", user_id="...", ocr_text=raw_text)
    print(f"Indexed {n} chunks")
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Optional

from supabase import Client

from backend.config.supabase_client import get_supabase_client
from backend.services.embeddings.interfaces import Embedder
from backend.services.embeddings.query_embedding import embed_texts
from backend.services.preprocessing.chunking import doc_to_chunks_with_metadata
from backend.services.preprocessing.text_cleaning import clean_full_text

logger = logging.getLogger(__name__)

_CHUNKS_TABLE = "report_chunks"

# Week-3 RAG ingestion improvement — embedding version tracking
# Bump this constant whenever the embedding model or chunking strategy changes
# to trigger re-embedding of affected chunks.
EMBEDDING_VERSION = os.getenv("EMBEDDING_VERSION", "bge-base-en-v1.5-w3")


def _chunk_id(report_id: str, chunk_index: int) -> str:
    """Return a deterministic UUID for a (report_id, chunk_index) pair.

    Using a hash-based UUID means that calling index_report() twice on the
    same report produces the same IDs, so ``upsert(on_conflict="id")``
    correctly *updates* existing rows instead of inserting duplicates.
    """
    key = f"{report_id}:{chunk_index}"
    # uuid5 is a SHA-1-based RFC-4122 name UUID — no extra imports needed.
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, key))


def index_report(
    report_id: str,
    user_id: str,
    ocr_text: str,
    *,
    client: Optional[Client] = None,
    embedder: Optional[Embedder] = None,
    source_filename: Optional[str] = None,
    source_url: Optional[str] = None, 
    page_number: Optional[int] = None, 
    # Week-3 RAG ingestion improvement — new metadata parameters
    report_date: Optional[str] = None,
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
    source_filename:
        Original filename of the uploaded report (e.g. ``"Lab_Report.pdf"``).
        Stored per chunk for citation metadata.  Falls back to a JOIN on
        ``medical_reports`` at retrieval time if ``None``.
    source_url:
        Public/signed URL to the source report in Supabase Storage.
        Stored per chunk for citation metadata.  Falls back via JOIN if ``None``.
    page_number:
        Optional page number hint.  Currently ``None`` for multi-page PDFs
        because the chunking pipeline does not yet track per-chunk page origin.
    report_date:
        ISO-8601 date string for the report (e.g. ``"2025-10-15"``).
        # Week-3 RAG ingestion improvement — stored per chunk for metadata.
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

    # ── 2. Chunk (Week-3: with section label metadata) ────────────────────────
    # Week-3 RAG ingestion improvement — use metadata-enriched chunking
    chunk_items = doc_to_chunks_with_metadata(
        cleaned, chunk_size=chunk_size, chunk_overlap=chunk_overlap,
    )
    if not chunk_items:
        logger.warning(
            "No chunks produced for report_id=%s; skipping indexing.", report_id
        )
        return 0

    # Extract plain text list for embedding
    chunks = [item["text"] for item in chunk_items]

    # ── 3. Embed ──────────────────────────────────────────────────────────────
    vectors = (
        embedder.embed_texts(chunks) if embedder is not None else embed_texts(chunks)
    )

    if len(vectors) != len(chunks):
        raise RuntimeError(
            f"Embedder returned {len(vectors)} vectors for {len(chunks)} chunks."
        )

    # ── 4. Delete stale chunks then insert fresh ──────────────────────────────
    # We delete all existing chunks for this report first so that if
    # re-indexing produces fewer chunks than before (e.g. OCR text was
    # corrected), no orphaned chunks from the old run survive in the DB.
    # The deterministic IDs below make subsequent upserts idempotent, but the
    # delete ensures the chunk count is always exactly what the current OCR
    # text produces — no more, no less.
    try:
        db.table(_CHUNKS_TABLE).delete().eq("report_id", report_id).execute()
    except Exception as exc:
        raise RuntimeError(
            f"Failed to clear old chunks for report_id={report_id}: {exc}"
        ) from exc

    rows = [
        {
            # Deterministic ID: same (report_id, chunk_index) → same UUID.
            # This makes the upsert truly idempotent if delete-first is ever
            # removed or if two processes race (last-writer-wins cleanly).
            "id": _chunk_id(report_id, idx),
            "report_id": report_id,
            "user_id": user_id,
            "chunk_index": idx,
            "chunk_text": chunk_item["text"],
            # PostgREST serialises Python lists to JSON arrays, which pgvector
            # accepts natively as vector literals.
            "embedding": vec,
            # Citation metadata (best-effort). If not provided during indexing,
            # the retrieval RPC can still fall back to medical_reports via JOIN.
            "source_filename": source_filename,
            "source_url": source_url,
            "page_number": page_number,
            # Week-3 RAG ingestion improvement — new metadata fields
            "section_label": chunk_item["section_label"],
            "report_date": report_date,
            "embedding_version": EMBEDDING_VERSION,
        }
        for idx, (chunk_item, vec) in enumerate(zip(chunk_items, vectors))
    ]

    try:
        db.table(_CHUNKS_TABLE).upsert(rows, on_conflict="id").execute()
    except Exception as exc:
        raise RuntimeError(f"Failed to upsert report chunks: {exc}") from exc

    logger.info("Indexed %d chunks for report_id=%s", len(rows), report_id)
    return len(rows)


# ---------------------------------------------------------------------------
# Week-3 RAG ingestion improvement — re-embedding support
# ---------------------------------------------------------------------------

def reindex_report(
    report_id: str,
    user_id: str,
    ocr_text: str,
    *,
    client: Optional[Client] = None,
    embedder: Optional[Embedder] = None,
    source_filename: Optional[str] = None,
    source_url: Optional[str] = None,
    page_number: Optional[int] = None,
    report_date: Optional[str] = None,
    chunk_size: int = 300,
    chunk_overlap: int = 50,
) -> int:
    """Re-embed and re-index a report, replacing all existing chunks.

    # Week-3 RAG ingestion improvement

    This is semantically identical to :func:`index_report` (which already
    deletes old chunks before inserting), but is provided as an explicit
    entry-point for callers that want to signal "re-embedding" intent —
    e.g. after the embedding model or chunking strategy has been updated.

    The ``embedding_version`` stored with each chunk is set to the current
    :data:`EMBEDDING_VERSION` constant, so stale rows from a previous version
    are easy to identify via a simple SQL query:

        SELECT DISTINCT report_id FROM report_chunks
        WHERE embedding_version != '<current>';
    """
    logger.info(
        "Re-indexing report_id=%s with embedding_version=%s",
        report_id, EMBEDDING_VERSION,
    )
    return index_report(
        report_id=report_id,
        user_id=user_id,
        ocr_text=ocr_text,
        client=client,
        embedder=embedder,
        source_filename=source_filename,
        source_url=source_url,
        page_number=page_number,
        report_date=report_date,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


def find_stale_reports(
    *, client: Optional[Client] = None,
) -> list[str]:
    """Return report_ids whose chunks have an outdated embedding_version.

    # Week-3 RAG ingestion improvement

    Useful for a background job that periodically re-embeds reports after
    the model or chunking strategy is updated.
    """
    db = client or get_supabase_client()
    try:
        resp = (
            db.table(_CHUNKS_TABLE)
            .select("report_id")
            .neq("embedding_version", EMBEDDING_VERSION)
            .execute()
        )
        rows = resp.data or []
        return list({r["report_id"] for r in rows})
    except Exception as exc:
        logger.warning("find_stale_reports failed: %s", exc)
        return []
