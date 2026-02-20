-- Migration 001: Add report_chunks table and match_report_chunks function
-- Apply this in your Supabase SQL editor or via psql.
-- Requires the pgvector extension to be available in your Postgres instance.
-- (Supabase projects have pgvector pre-installed.)

-- ── 0. Enable pgvector ────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS vector;

-- ── 1. report_chunks table ───────────────────────────────────────────────────
-- Stores cleaned, chunked text derived from OCR reports, together with their
-- vector embeddings produced by BAAI/bge-base-en-v1.5 (768 dimensions).
-- Rows are deleted automatically when their parent medical_report is removed.

CREATE TABLE IF NOT EXISTS report_chunks (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id    UUID        NOT NULL REFERENCES medical_reports(id) ON DELETE CASCADE,
    user_id      UUID        NOT NULL,
    chunk_index  INT         NOT NULL,          -- sequential position within the report
    chunk_text   TEXT        NOT NULL,
    embedding    vector(768),                   -- BAAI/bge-base-en-v1.5 output dimension
    created_at   TIMESTAMP   DEFAULT now()
);

COMMENT ON TABLE report_chunks IS
'Cleaned, chunked text and vector embeddings derived from OCR medical reports. '
'Used for semantic (RAG) retrieval.';

COMMENT ON COLUMN report_chunks.embedding IS
'768-dimensional L2-normalised embedding (BAAI/bge-base-en-v1.5). '
'Cosine similarity is computed via inner product because vectors are unit length.';

-- ── 2. Indexes ───────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_report_chunks_report_id
    ON report_chunks (report_id);

CREATE INDEX IF NOT EXISTS idx_report_chunks_user_id
    ON report_chunks (user_id);

-- HNSW index: sub-linear ANN lookup with cosine distance.
-- Preferred over IVFFlat when the row count is <5 M and recall matters.
-- ef_construction and m can be tuned later; these are safe defaults.
CREATE INDEX IF NOT EXISTS idx_report_chunks_embedding_hnsw
    ON report_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ── 3. match_report_chunks RPC function ──────────────────────────────────────
-- Called from Python via:  client.rpc("match_report_chunks", {...}).execute()
-- Returns the top-k most similar chunks for a user / query embedding pair.

CREATE OR REPLACE FUNCTION match_report_chunks(
    query_embedding   vector(768),
    match_user_id     uuid,
    match_count       int     DEFAULT 5,
    match_threshold   float   DEFAULT 0.4
)
RETURNS TABLE (
    id           uuid,
    report_id    uuid,
    chunk_index  int,
    chunk_text   text,
    similarity   float
)
LANGUAGE plpgsql
STABLE              -- read-only; lets the planner cache the plan
AS $$
BEGIN
    RETURN QUERY
    SELECT
        rc.id,
        rc.report_id,
        rc.chunk_index,
        rc.chunk_text,
        -- <=> is cosine *distance*; 1 - distance = cosine *similarity*
        (1.0 - (rc.embedding <=> query_embedding))::float AS similarity
    FROM  report_chunks rc
    WHERE rc.user_id = match_user_id
      AND (1.0 - (rc.embedding <=> query_embedding)) >= match_threshold
    ORDER BY rc.embedding <=> query_embedding   -- ascending distance = descending similarity
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_report_chunks IS
'Returns the top-k most semantically similar report chunks for a given user '
'and query embedding, filtered by a minimum cosine-similarity threshold.';
