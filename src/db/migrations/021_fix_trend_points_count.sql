-- Migration 021: Fix trend_points count and summary window edge cases
--
-- Problems fixed
-- ---------------
-- FIX C — "Day 8" phantom in chart
--   The previous ARRAY_AGG in daily_trends collected however many UTC calendar-
--   date buckets existed in the data window.  For a 7-day window ending mid-day
--   there are 8 distinct UTC dates (today + 7 prior days), producing 8 entries
--   in trend_points.  The Android chart rendered all 8, and the label array (7
--   entries) had no label for the 8th point, falling back to the "Day 8" tooltip.
--
--   Fix: slice the aggregated array to at most p_days entries:
--       (ARRAY_AGG(...))[1:p_days]
--
-- FIX D — SpO2 / Sleep missing from summary (UTC rolling-window edge case)
--   The old filter  recorded_at >= NOW() - INTERVAL '1 day' * p_days  is a
--   rolling UTC window.  When the Android app sends period-bucket timestamps
--   WITHOUT a timezone offset (the bug fixed on the Android side in this same
--   release), PostgreSQL used to interpret them as UTC midnight.  For a UTC+5:30
--   user, local midnight = 18:30 UTC the day before, so some valid Day-1 records
--   landed just outside the rolling window and were silently excluded.
--
--   Even after the Android timestamp fix (offset now attached), data inserted
--   before the fix still lives at the "wrong" UTC time.  Expanding the window
--   by 1 extra day catches those legacy records and any future edge cases from
--   DST transitions or clock skew.
--
--   Fix: expand the filtered CTE window to (p_days + 1) days.  trend_points is
--   still clamped to p_days entries, so the chart always shows exactly 7 bars.

DROP FUNCTION IF EXISTS get_vitals_summary(UUID, INTEGER);

CREATE FUNCTION get_vitals_summary(
    p_user_id UUID,
    p_days    INTEGER DEFAULT 7
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
    -- FIX D: expand the raw window by 1 day so records that sit at local Day-1
    -- midnight (stored slightly before the strict rolling-window boundary due to
    -- timezone offset) are not silently dropped.
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

    -- Overall per-metric aggregates across the (slightly wider) window.
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

    -- FIX C: group only the strict p_days window for daily buckets so the
    -- resulting ARRAY_AGG can never produce more than p_days entries.
    daily_rollup AS (
        SELECT
            f.metric_type,
            DATE(f.recorded_at) AS record_date,
            ROUND(AVG(f.value)::NUMERIC, 2) AS daily_avg
        FROM filtered AS f
        WHERE f.recorded_at >= NOW() - INTERVAL '1 day' * p_days
        GROUP BY f.metric_type, DATE(f.recorded_at)
    ),

    -- FIX C: slice the array to at most p_days entries so the Android chart's
    -- label array (also p_days long) always aligns with the data points.
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
        -- latest_value is scoped to the strict p_days window (no stale values).
        (
            SELECT wv2.value
            FROM wearable_vitals AS wv2
            WHERE wv2.user_id   = p_user_id
              AND wv2.metric_type = mr.metric_type
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
'Returns per-metric wearable vitals aggregates for the last N days. '
'FIX C: trend_points array is sliced to exactly p_days entries, preventing the '
'"Day 8" phantom bar in the Android chart when UTC midnight boundaries split an '
'extra day. '
'FIX D: the raw data window is extended by 1 day to catch records that fell just '
'outside the strict rolling window due to timezone-offset storage inconsistencies '
'from before migration 021.';

GRANT EXECUTE ON FUNCTION get_vitals_summary(UUID, INTEGER)
TO anon, authenticated, service_role;
