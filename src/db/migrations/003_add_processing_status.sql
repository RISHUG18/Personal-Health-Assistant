    -- Migration 003: add pipeline processing status to medical_reports
    --
    -- Makes ocr_text nullable so a placeholder row can be created before OCR
    -- runs (supporting the async /reports/ingest endpoint).  Adds
    -- processing_status + processing_error so clients can poll progress.

    ALTER TABLE medical_reports
        ALTER COLUMN ocr_text DROP NOT NULL;

    ALTER TABLE medical_reports
        ADD COLUMN IF NOT EXISTS processing_status TEXT NOT NULL DEFAULT 'pending'
            CHECK (processing_status IN ('pending', 'ocr_complete', 'done', 'failed'));

    ALTER TABLE medical_reports
        ADD COLUMN IF NOT EXISTS processing_error TEXT;

    COMMENT ON COLUMN medical_reports.processing_status IS
    'Tracks the async pipeline stage: pending → ocr_complete → done (or failed).';

    COMMENT ON COLUMN medical_reports.processing_error IS
    'Human-readable error message when processing_status = ''failed''.';
