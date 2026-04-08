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


CREATE TABLE lab_results (
    id UUID PRIMARY KEY,
    report_id UUID REFERENCES medical_reports(id) ON DELETE CASCADE,

    test_name TEXT NOT NULL,
    value NUMERIC,
    text_value TEXT,
    unit TEXT,
    reference_range TEXT,
    abnormal_flag BOOLEAN,

    extracted_from_page INT
);

CREATE INDEX idx_lab_results_report_id ON lab_results(report_id);

COMMENT ON TABLE lab_results IS
'Structured numeric lab values extracted from OCR without interpretation.';


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

    ocr_text_snippet TEXT
);

CREATE INDEX idx_alert_evidence_alert_id ON alert_evidence(alert_id);

COMMENT ON TABLE alert_evidence IS
'Links alerts to verifiable evidence from OCR text or lab results.';
