-- Migration 013: Add age to users
-- Note: age is typically calculated from date_of_birth, but adding explicit column per user requirements.

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS age INT;

COMMENT ON COLUMN users.age IS
'Explicit user age field (derived typically but explicitly required).';
