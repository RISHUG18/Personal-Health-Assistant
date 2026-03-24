-- Migration 006: Add environmental_evidence to alert_evidence
-- Stores JSON snapshots of environmental conditions at time of alert generation.

ALTER TABLE alert_evidence
ADD COLUMN IF NOT EXISTS environmental_evidence JSONB;

COMMENT ON COLUMN alert_evidence.environmental_evidence IS
'JSON object containing AQI, temperature, and humidity at the time the alert was generated.';
