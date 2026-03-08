-- Migration 003: Week-3 RAG ingestion improvement
-- Add section_label, report_date, and embedding_version columns to report_chunks
-- and return them from the match_report_chunks RPC function.
-- Apply this after 002_add_report_chunk_metadata.sql

-- ── 1. Extend report_chunks with section / version metadata ──────────────────

ALTER TABLE IF EXISTS report_chunks
    ADD COLUMN IF NOT EXISTS section_label      TEXT DEFAULT 'other',
    ADD COLUMN IF NOT EXISTS report_date         DATE,
    ADD COLUMN IF NOT EXISTS embedding_version   TEXT;

COMMENT ON COLUMN report_chunks.section_label IS
'Week-3: Heuristic section label for the chunk (blood_test, sleep_data, imaging, vitals, summary, other).';

COMMENT ON COLUMN report_chunks.report_date IS
'Week-3: ISO date of the parent medical report, denormalised per chunk for metadata retrieval.';

COMMENT ON COLUMN report_chunks.embedding_version IS
'Week-3: Identifier for the embedding model + chunking strategy version used to produce this chunk''s embedding. '
'Used to detect stale embeddings that need re-generation.';

-- ── 2. Index on embedding_version for efficient staleness queries ────────────

CREATE INDEX IF NOT EXISTS idx_report_chunks_embedding_version
    ON report_chunks (embedding_version);

-- ── 3. Update match_report_chunks to return new metadata columns ─────────────
-- Keeps the same function name/signature so existing callers (pgvector_retrieval.py)
-- continue to work without code changes.

CREATE OR REPLACE FUNCTION match_report_chunks(
    query_embedding   vector(768),
    match_user_id     uuid,
    match_count       int     DEFAULT 5,
    match_threshold   float   DEFAULT 0.4
)
RETURNS TABLE (
    id                uuid,
    report_id         uuid,
    chunk_index       int,
    chunk_text        text,
    source_filename   text,
    source_url        text,
    page_number       int,
    section_label     text,
    report_date       date,
    embedding_version text,
    similarity        float
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT
        rc.id,
        rc.report_id,
        rc.chunk_index,
        rc.chunk_text,
        COALESCE(rc.source_filename, mr.source_file_name) AS source_filename,
        COALESCE(rc.source_url, mr.source_url)           AS source_url,
        rc.page_number,
        -- Week-3 RAG ingestion improvement — new metadata columns
        COALESCE(rc.section_label, 'other')               AS section_label,
        COALESCE(rc.report_date, mr.report_date::date)    AS report_date,
        rc.embedding_version,
        (1.0 - (rc.embedding <=> query_embedding))::float AS similarity
    FROM  report_chunks rc
    LEFT JOIN medical_reports mr ON mr.id = rc.report_id
    WHERE rc.user_id = match_user_id
      AND (1.0 - (rc.embedding <=> query_embedding)) >= match_threshold
    ORDER BY rc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_report_chunks IS
'Returns the top-k most semantically similar report chunks for a given user '
'and query embedding.  Week-3: now includes section_label, report_date, '
'and embedding_version in the result set.';
