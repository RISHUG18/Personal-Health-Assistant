-- Migration 018: Create the get_trended_labs Postgres RPC
--
-- Purpose
-- -------
-- Returns the 3 most recent lab readings per unique canonical test name for a
-- given user, ordered chronologically (newest first).  The result set is
-- designed to feed directly into the LLM context builder's longitudinal view.
--
-- Design notes
-- ------------
-- * lab_results does NOT store a date directly; the test date is sourced from
--   medical_reports.report_date via the report_id foreign key.
-- * A CTE with ROW_NUMBER() OVER (PARTITION BY test_name ORDER BY report_date DESC)
--   provides a deterministic, per-test ranking.
-- * Only rows where rn <= 3 are returned to the caller.
-- * The function is marked SECURITY DEFINER so it can be executed via the
--   Supabase anon key while still enforcing the p_user_id filter.

CREATE OR REPLACE FUNCTION get_trended_labs(p_user_id UUID)
RETURNS TABLE (
    test_name   TEXT,
    test_value  NUMERIC,
    unit        TEXT,
    record_date DATE
)
LANGUAGE sql
STABLE
SECURITY DEFINER
AS $$
    WITH ranked_labs AS (
        SELECT
            lr.test_name,
            lr.value                                                         AS test_value,
            lr.unit,
            mr.report_date                                                   AS record_date,
            ROW_NUMBER() OVER (
                PARTITION BY lr.test_name
                ORDER BY mr.report_date DESC NULLS LAST
            )                                                                AS rn
        FROM lab_results  lr
        JOIN medical_reports mr
          ON mr.id = lr.report_id
        WHERE mr.user_id = p_user_id
          AND lr.value   IS NOT NULL
    )
    SELECT
        test_name,
        test_value,
        unit,
        record_date
    FROM ranked_labs
    WHERE rn <= 3
    ORDER BY test_name, record_date DESC;
$$;

-- Grant execute to the authenticated and service-role keys used by Supabase.
GRANT EXECUTE ON FUNCTION get_trended_labs(UUID) TO anon, authenticated, service_role;
