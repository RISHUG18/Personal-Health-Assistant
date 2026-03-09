-- Migration 004: Week-4 Retrieval Optimization
-- Add optional filter_section_label parameter to match_report_chunks RPC
-- so section-level filtering can be pushed down to Postgres instead of
-- being done client-side.  The parameter defaults to NULL (no filter).
-- Apply this after 003_add_chunk_section_metadata.sql

-- ── 1. Index on section_label for efficient filtering ────────────────────────

CREATE INDEX IF NOT EXISTS idx_report_chunks_section_label
    ON report_chunks (section_label);

-- ── 2. Composite index for user + section scoped queries ─────────────────────

CREATE INDEX IF NOT EXISTS idx_report_chunks_user_section
    ON report_chunks (user_id, section_label);

-- ── 3. Re-create match_report_chunks with optional section filter ────────────
-- The new parameter filter_section_label defaults to NULL.
-- When NULL, all sections are returned (backward-compatible).
-- When set (e.g. 'blood_test'), only chunks with that section_label match.

CREATE OR REPLACE FUNCTION match_report_chunks(
    query_embedding         vector(768),
    match_user_id           uuid,
    match_count             int     DEFAULT 5,
    match_threshold         float   DEFAULT 0.4,
    filter_section_label    text    DEFAULT NULL     -- Week-4: optional section filter
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
        COALESCE(rc.section_label, 'other')               AS section_label,
        COALESCE(rc.report_date, mr.report_date::date)    AS report_date,
        rc.embedding_version,
        (1.0 - (rc.embedding <=> query_embedding))::float AS similarity
    FROM  report_chunks rc
    LEFT JOIN medical_reports mr ON mr.id = rc.report_id
    WHERE rc.user_id = match_user_id
      AND (1.0 - (rc.embedding <=> query_embedding)) >= match_threshold
      -- Week-4 Retrieval Optimization: optional section_label filter
      AND (filter_section_label IS NULL OR rc.section_label = filter_section_label)
    ORDER BY rc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_report_chunks IS
'Returns the top-k most semantically similar report chunks for a given user '
'and query embedding.  Week-3: includes section_label, report_date, '
'embedding_version.  Week-4: supports optional section_label filtering via '
'the filter_section_label parameter (NULL = no filter).';
