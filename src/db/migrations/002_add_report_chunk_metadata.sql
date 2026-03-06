-- Migration 002: Add metadata columns to report_chunks and return them from match_report_chunks
-- Apply this after 001_add_report_chunks.sql

-- 1) Extend report_chunks with citation metadata
ALTER TABLE IF EXISTS report_chunks
    ADD COLUMN IF NOT EXISTS source_filename TEXT,
    ADD COLUMN IF NOT EXISTS source_url TEXT,
    ADD COLUMN IF NOT EXISTS page_number INT;

COMMENT ON COLUMN report_chunks.source_filename IS
'Original report filename used for citations (mirrors medical_reports.source_file_name).';

COMMENT ON COLUMN report_chunks.source_url IS
'Public/signed URL to the source report used for citations (mirrors medical_reports.source_url).';

COMMENT ON COLUMN report_chunks.page_number IS
'Optional page number for the chunk, if available (best-effort).';


-- 2) Return citation metadata from the pgvector RPC function
-- NOTE: We keep the function name/signature the same so existing clients work.
CREATE OR REPLACE FUNCTION match_report_chunks(
    query_embedding   vector(768),
    match_user_id     uuid,
    match_count       int     DEFAULT 5,
    match_threshold   float   DEFAULT 0.4
)
RETURNS TABLE (
    id              uuid,
    report_id       uuid,
    chunk_index     int,
    chunk_text      text,
    source_filename text,
    source_url      text,
    page_number     int,
    similarity      float
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
        (1.0 - (rc.embedding <=> query_embedding))::float AS similarity
    FROM  report_chunks rc
    LEFT JOIN medical_reports mr ON mr.id = rc.report_id
    WHERE rc.user_id = match_user_id
      AND (1.0 - (rc.embedding <=> query_embedding)) >= match_threshold
    ORDER BY rc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
