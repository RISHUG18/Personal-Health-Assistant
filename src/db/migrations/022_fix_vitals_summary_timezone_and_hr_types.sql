-- Migration 022: Fix vitals summary timezone bucketing and add heart_rate_min/max types
--
-- Problems fixed
-- ---------------
-- FIX-TZ  — Daily trend buckets off by one day for non-UTC users
--   The previous daily_rollup CTE grouped by DATE(recorded_at) using the
--   database default timezone (UTC).  For a UTC+5:30 user, a step reading
--   for local midnight 2026-04-14T00:00:00+05:30 is stored as
--   2026-04-13T18:30:00Z, so DATE() places it into April 13 instead of
--   April 14, shifting every trend bar one day earlier than Google Fit.
--
--   Fix: expand the RPC signature with an optional p_timezone TEXT parameter
--   (default 'UTC' for backwards compatibility).  The daily_rollup CTE now
--   buckets by DATE(recorded_at AT TIME ZONE p_timezone) so calendar days
--   align with the user's local clock, matching Google Fit.
--
-- FIX-HR  — heart_rate summary now correctly computes min/max across the NEW
--   dedicated heart_rate_min and heart_rate_max metric types.
--   The Android app (post-fix) sends three readings per day:
--     • metric_type = 'heart_rate'     → daily weighted average (BPM_AVG)
--     • metric_type = 'heart_rate_min' → true lowest BPM sample that day
--     • metric_type = 'heart_rate_max' → true highest BPM sample that day
--   The old function computed MIN/MAX from daily average rows, which gave
--   min = lowest-daily-average (not true min) and was consistently higher
--   than Google Fit's reported minimum.  The new function returns each
--   metric type independently; the Android UI synthesises the display card
--   by combining heart_rate (avg) with heart_rate_min/max (true range).

DROP FUNCTION IF EXISTS get_vitals_summary(UUID, INTEGER);
DROP FUNCTION IF EXISTS get_vitals_summary(UUID, INTEGER, TEXT);

CREATE FUNCTION get_vitals_summary(
    p_user_id  UUID,
    p_days     INTEGER DEFAULT 7,
    p_timezone TEXT    DEFAULT 'UTC'
)
RETURNS TABLE (
    metric_type  TEXT,
    avg_value    NUMERIC,
    min_value    NUMERIC,
    max_value    NUMERIC,
    latest_value NUMERIC,
    trend_points NUMERIC[],
    sample_count BIGINT,
    unit         TEXT
)
LANGUAGE sql
STABLE
AS $$
    -- FIX-TZ + FIX-D: Expand raw window by 1 day to catch legacy records that
    -- were stored at slightly wrong UTC times before the Android timezone fix.
    WITH filtered AS (
        SELECT
            wv.metric_type,
            wv.value,
            wv.unit,
            wv.recorded_at
        FROM wearable_vitals AS wv
        WHERE wv.user_id = p_user_id
          AND wv.recorded_at >= NOW() - INTERVAL '1 day' * (p_days + 1)
    ),

    -- Overall per-metric aggregates (avg, min, max, count) across the wider window.
    metric_rollup AS (
        SELECT
            f.metric_type,
            ROUND(AVG(f.value)::NUMERIC, 2) AS avg_value,
            MIN(f.value)                     AS min_value,
            MAX(f.value)                     AS max_value,
            COUNT(*)                         AS sample_count,
            MAX(f.unit)                      AS unit
        FROM filtered AS f
        GROUP BY f.metric_type
    ),

    -- FIX-TZ: Group the strict p_days window into LOCAL calendar days using
    -- p_timezone so each daily bucket matches the user's clock, not UTC.
    daily_rollup AS (
        SELECT
            f.metric_type,
            DATE(f.recorded_at AT TIME ZONE p_timezone) AS record_date,
            ROUND(AVG(f.value)::NUMERIC, 2)             AS daily_avg
        FROM filtered AS f
        WHERE f.recorded_at >= NOW() - INTERVAL '1 day' * p_days
        GROUP BY f.metric_type,
                 DATE(f.recorded_at AT TIME ZONE p_timezone)
    ),

    -- FIX-C: Slice the array to at most p_days entries.
    daily_trends AS (
        SELECT
            d.metric_type,
            (ARRAY_AGG(d.daily_avg ORDER BY d.record_date))[1:p_days] AS trend_points
        FROM daily_rollup AS d
        GROUP BY d.metric_type
    )

    SELECT
        mr.metric_type,
        mr.avg_value,
        mr.min_value,
        mr.max_value,
        -- latest_value scoped to the strict p_days window (no stale values).
        (
            SELECT wv2.value
            FROM wearable_vitals AS wv2
            WHERE wv2.user_id    = p_user_id
              AND wv2.metric_type  = mr.metric_type
              AND wv2.recorded_at >= NOW() - INTERVAL '1 day' * p_days
            ORDER BY wv2.recorded_at DESC
            LIMIT 1
        ) AS latest_value,
        COALESCE(dt.trend_points, ARRAY[]::NUMERIC[]) AS trend_points,
        mr.sample_count,
        mr.unit
    FROM metric_rollup AS mr
    LEFT JOIN daily_trends AS dt
           ON dt.metric_type = mr.metric_type
    ORDER BY mr.metric_type;
$$;

COMMENT ON FUNCTION get_vitals_summary IS
'Returns per-metric wearable vitals aggregates for the last N days.
FIX-TZ  (022): daily_rollup now buckets by DATE(recorded_at AT TIME ZONE p_timezone)
               so trend bars align with the user''s local calendar, not UTC.
               Pass the IANA timezone string, e.g. ''Asia/Kolkata''. Default: ''UTC''.
FIX-HR  (022): heart_rate_min / heart_rate_max are returned as independent rows so
               the Android UI can show true per-day BPM range from Health Connect
               aggregation rather than min/max of daily averages.
FIX-C   (021): trend_points sliced to p_days entries.
FIX-D   (021): raw window expanded by +1 day for legacy pre-fix records.';

GRANT EXECUTE ON FUNCTION get_vitals_summary(UUID, INTEGER, TEXT)
TO anon, authenticated, service_role;
