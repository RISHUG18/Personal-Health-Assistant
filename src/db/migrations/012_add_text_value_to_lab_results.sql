-- Migration 012: Add text_value to lab_results
-- Allows storing non-numeric lab result values extracted by Gemini (e.g. 'Positive', 'Type O+')
-- while preserving the existing NUMERIC value column.

ALTER TABLE lab_results 
ADD COLUMN IF NOT EXISTS text_value TEXT;

COMMENT ON COLUMN lab_results.text_value IS
'Stores non-numeric string values extracted by Gemini for Qualitative tests.';
