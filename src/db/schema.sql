CREATE TABLE medical_reports (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    report_date DATE,
    report_type TEXT,
    source_file_name TEXT,
    source_url TEXT,

    -- OCR storage (DO NOT MODIFY CONTENT)
    ocr_text TEXT NOT NULL,
    ocr_engine TEXT,
    ocr_engine_version TEXT,
    ocr_confidence NUMERIC,

    created_at TIMESTAMP DEFAULT now()
);

COMMENT ON TABLE medical_reports IS
'Stores full, unmodified OCR output for uploaded medical PDFs. OCR text is treated as immutable.';


CREATE TABLE tests_master (
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

CREATE TABLE test_aliases (
    alias TEXT PRIMARY KEY,
    code TEXT NOT NULL REFERENCES tests_master(code) ON DELETE CASCADE
);

CREATE INDEX idx_test_aliases_code ON test_aliases(code);

CREATE TABLE test_units (
    code TEXT NOT NULL REFERENCES tests_master(code) ON DELETE CASCADE,
    unit TEXT NOT NULL,
    PRIMARY KEY (code, unit)
);

CREATE TABLE lab_results (
    id UUID PRIMARY KEY,
    report_id UUID REFERENCES medical_reports(id) ON DELETE CASCADE,

    test_name TEXT NOT NULL,
    normalization_confidence NUMERIC(4, 3),
    value NUMERIC,
    text_value TEXT,
    unit TEXT,
    reference_range TEXT,
    abnormal_flag BOOLEAN,

    extracted_from_page INT
);

CREATE INDEX idx_lab_results_report_id ON lab_results(report_id);

COMMENT ON TABLE lab_results IS
'Structured lab values stored with normalized test identifiers.';

CREATE TABLE unmapped_tests (
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
    created_at TIMESTAMP DEFAULT now()
);


CREATE TABLE alerts (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    severity TEXT CHECK (severity IN ('low', 'medium', 'high')),
    reason TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

COMMENT ON TABLE alerts IS
'Alerts generated via deterministic rules over structured data.';


CREATE TABLE alert_evidence (
    id UUID PRIMARY KEY,
    alert_id UUID REFERENCES alerts(id) ON DELETE CASCADE,

    report_id UUID REFERENCES medical_reports(id),
    lab_result_id UUID REFERENCES lab_results(id),

    ocr_text_snippet TEXT,
    environmental_evidence JSONB
);

CREATE INDEX idx_alert_evidence_alert_id ON alert_evidence(alert_id);

COMMENT ON TABLE alert_evidence IS
'Links alerts to verifiable evidence from OCR text or lab results.';
