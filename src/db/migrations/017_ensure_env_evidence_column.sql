-- Migration 017: Ensure environmental evidence support on alert_evidence
--
-- Some deployments may have been created from an older schema snapshot where
-- alert_evidence.environmental_evidence was not present. This migration is
-- idempotent and guarantees the column exists.

ALTER TABLE IF EXISTS alert_evidence
ADD COLUMN IF NOT EXISTS environmental_evidence JSONB;

COMMENT ON COLUMN alert_evidence.environmental_evidence IS
'JSON object containing AQI, temperature, humidity, and source metadata captured when the alert was generated.';
