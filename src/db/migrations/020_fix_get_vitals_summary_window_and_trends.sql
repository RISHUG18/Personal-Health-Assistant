-- Migration 020: Fix get_vitals_summary windowing + add daily trend points
--
-- Fixes
-- -----
-- 1) latest_value now respects p_days (no stale values outside the summary window).
-- 2) Adds trend_points (numeric[]) with chronological daily averages per metric.

DROP FUNCTION IF EXISTS get_vitals_summary(UUID, INTEGER);

CREATE FUNCTION get_vitals_summary(
    p_user_id UUID,
    p_days INTEGER DEFAULT 7
)
RETURNS TABLE (
    metric_type TEXT,
    avg_value NUMERIC,
    min_value NUMERIC,
    max_value NUMERIC,
    latest_value NUMERIC,
    trend_points NUMERIC[],
    sample_count BIGINT,
    unit TEXT
)
LANGUAGE sql
STABLE
AS $$
    WITH filtered AS (
        SELECT
            wv.metric_type,
            wv.value,
            wv.unit,
            wv.recorded_at
        FROM wearable_vitals AS wv
        WHERE wv.user_id = p_user_id
          AND wv.recorded_at >= NOW() - INTERVAL '1 day' * p_days
    ),
    metric_rollup AS (
        SELECT
            f.metric_type,
            ROUND(AVG(f.value)::NUMERIC, 2) AS avg_value,
            MIN(f.value) AS min_value,
            MAX(f.value) AS max_value,
            COUNT(*) AS sample_count,
            MAX(f.unit) AS unit
        FROM filtered AS f
        GROUP BY f.metric_type
    ),
    daily_rollup AS (
        SELECT
            f.metric_type,
            DATE(f.recorded_at) AS record_date,
            ROUND(AVG(f.value)::NUMERIC, 2) AS daily_avg
        FROM filtered AS f
        GROUP BY f.metric_type, DATE(f.recorded_at)
    ),
    daily_trends AS (
        SELECT
            d.metric_type,
            ARRAY_AGG(d.daily_avg ORDER BY d.record_date) AS trend_points
        FROM daily_rollup AS d
        GROUP BY d.metric_type
    )
    SELECT
        mr.metric_type,
        mr.avg_value,
        mr.min_value,
        mr.max_value,
        (
            SELECT wv2.value
            FROM wearable_vitals AS wv2
            WHERE wv2.user_id = p_user_id
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
'Returns per-metric wearable vitals aggregates for the last N days, including '
'window-scoped latest_value and chronological daily trend_points arrays.';

GRANT EXECUTE ON FUNCTION get_vitals_summary(UUID, INTEGER)
TO anon, authenticated, service_role;
