-- Migration 014: Drop redundant `age` column from users table
--
-- Rationale
-- ---------
-- The `age` column (added in migration 013) is a derived value that becomes
-- stale the moment the user's birthday passes.  Storing a static integer is an
-- anti-pattern when the authoritative `date_of_birth` field (DATE column) is
-- already present in the same row (migration 000).
--
-- Age is now calculated at query time in the application layer:
--   backend/services/context/data_fetchers.py :: _calculate_age(date_of_birth)
--
-- This ensures the value Gemini receives in the context payload is always
-- accurate without any background job or manual update.
--
-- To apply: run this SQL in the Supabase SQL editor.
-- Safe to re-run: IF EXISTS prevents errors on a clean schema.

ALTER TABLE users
    DROP COLUMN IF EXISTS age;

COMMENT ON COLUMN users.date_of_birth IS
'Date of birth (ISO date).  Age is derived at query time by the application — '
'do not store a static age column alongside this field.';
