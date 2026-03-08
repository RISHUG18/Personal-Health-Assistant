-- Migration 003: Ensure alerts and alert_evidence tables exist
-- These tables are defined in the base schema.sql but this migration
-- makes them safely re-runnable for environments that apply migrations
-- incrementally (e.g., staging, new developer setups).
-- Run with: psql $DATABASE_URL -f 003_create_alerts_tables.sql

-- ── alerts ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id          UUID PRIMARY KEY,
    user_id     UUID    NOT NULL,
    severity    TEXT    CHECK (severity IN ('low', 'medium', 'high')),
    reason      TEXT    NOT NULL,
    created_at  TIMESTAMP DEFAULT now()
);

COMMENT ON TABLE alerts IS
'Alerts generated via deterministic rules over structured lab data. '
'Represent system signals, not medical diagnoses.';

COMMENT ON COLUMN alerts.severity IS
'low = informational | medium = warrants attention | high = prompt review';

-- ── alert_evidence ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alert_evidence (
    id               UUID PRIMARY KEY,
    alert_id         UUID REFERENCES alerts(id) ON DELETE CASCADE,
    report_id        UUID REFERENCES medical_reports(id),
    lab_result_id    UUID REFERENCES lab_results(id),
    ocr_text_snippet TEXT
);

CREATE INDEX IF NOT EXISTS idx_alert_evidence_alert_id
    ON alert_evidence (alert_id);

CREATE INDEX IF NOT EXISTS idx_alerts_user_id
    ON alerts (user_id);

COMMENT ON TABLE alert_evidence IS
'Explicit, verifiable evidence linking each alert to a lab result '
'and/or a verbatim OCR text snippet.';
