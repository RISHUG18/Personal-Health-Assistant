CREATE TABLE IF NOT EXISTS tests_master (
    code TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL CHECK (
        category IN (
            'hematology',
            'liver_function',
            'kidney_function',
            'diabetes',
            'lipid_profile',
            'thyroid',
            'vitamins_minerals',
            'urine_analysis',
            'others'
        )
    )
);

CREATE TABLE IF NOT EXISTS test_aliases (
    alias TEXT PRIMARY KEY,
    code TEXT NOT NULL REFERENCES tests_master(code) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_test_aliases_code ON test_aliases(code);

CREATE TABLE IF NOT EXISTS test_units (
    code TEXT NOT NULL REFERENCES tests_master(code) ON DELETE CASCADE,
    unit TEXT NOT NULL,
    PRIMARY KEY (code, unit)
);

CREATE TABLE IF NOT EXISTS unmapped_tests (
    id UUID PRIMARY KEY,
    report_id UUID REFERENCES medical_reports(id) ON DELETE CASCADE,
    source_lab_result_id UUID UNIQUE,
    raw_test_name TEXT NOT NULL,
    normalized_input TEXT,
    suggested_code TEXT,
    suggested_name TEXT,
    confidence NUMERIC(4, 3) NOT NULL DEFAULT 0,
    value NUMERIC,
    text_value TEXT,
    unit TEXT,
    reference_range TEXT,
    extracted_from_page INT,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

ALTER TABLE lab_results
    ADD COLUMN IF NOT EXISTS normalization_confidence NUMERIC(4, 3);

ALTER TABLE lab_results
    DROP COLUMN IF EXISTS canonical_name,
    DROP COLUMN IF EXISTS test_code;
