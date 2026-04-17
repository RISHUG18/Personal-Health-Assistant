-- Migration 023: Fix steps aggregation — use MAX per day, stats from daily totals
--
-- Problems fixed
-- ---------------
-- FIX-STEPS-AVG
--   The metric_rollup CTE used AVG(value) over ALL raw rows for a metric type.
--   For steps this is wrong in two ways:
--     1. Multiple rows may exist for the same calendar day due to:
--        a) Earlier partial-count sync (e.g. 5,000 steps at 10 AM) stored with
--           ignore_duplicates=True, then the full-day total (12,000 steps at 8 PM)
--           was skipped.  Both rows coexist if they have different timestamps.
--        b) endTime-based timestamps from a previous code version coexist with
--           startTime-based timestamps from the current version.
--     2. AVG across 7 daily totals is semantically wrong for "Typical" — it should
--        be the average of each day's TOTAL, not the average of all raw rows.
--
--   Fix: restructure the query so that:
--     Step 1 — daily_rollup: MAX(value) per (metric_type, local-date)
--              MAX picks the highest value seen for a day, which is the most
--              complete step total when stale partial rows exist.
--     Step 2 — metric_rollup: AVG/MIN/MAX/COUNT computed over daily totals.
--              avg_value = mean of daily totals    → "Typical" daily steps
--              min_value = lowest  daily total     → least active day
--              max_value = highest daily total     → most active day
--
-- FIX-DEEP-SLEEP (bonus)
--   The same MAX(value) in daily_rollup means that on a day where old code
--   wrote deep_sleep_minutes=0 alongside a real reading of 45, MAX picks 45.
--   This partially fixes deep sleep even before the DB cleanup migration.

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
    -- Raw rows inside the window (slightly wider to catch timezone-edge records).
    WITH filtered AS (
        SELECT
            wv.metric_type,
            wv.value,
            wv.unit,
            wv.recorded_at
        FROM wearable_vitals AS wv
        WHERE wv.user_id    = p_user_id
          AND wv.recorded_at >= NOW() - INTERVAL '1 day' * (p_days + 1)
    ),

    -- FIX-STEPS-AVG Step 1:
    -- Collapse all rows for the same (metric_type, local calendar day) into a
    -- single representative value using MAX.  For steps and calories this picks
    -- the highest cumulative total seen that day, discarding stale partial counts.
    -- For heart_rate each day already has exactly one row so MAX = that value.
    daily_rollup AS (
        SELECT
            f.metric_type,
            DATE(f.recorded_at AT TIME ZONE p_timezone) AS record_date,
            MAX(f.value)                                 AS daily_max,
            MAX(f.unit)                                  AS unit
        FROM filtered AS f
        WHERE f.recorded_at >= NOW() - INTERVAL '1 day' * p_days
        GROUP BY f.metric_type,
                 DATE(f.recorded_at AT TIME ZONE p_timezone)
    ),

    -- FIX-STEPS-AVG Step 2:
    -- Compute per-metric statistics over daily values, not over raw rows.
    -- avg_value = average of daily totals  (e.g. "typical daily steps")
    -- min_value = lowest  daily total      (least  active / slowest day)
    -- max_value = highest daily total      (most active / busiest day)
    metric_rollup AS (
        SELECT
            d.metric_type,
            ROUND(AVG(d.daily_max)::NUMERIC, 2) AS avg_value,
            MIN(d.daily_max)                     AS min_value,
            MAX(d.daily_max)                     AS max_value,
            COUNT(*)                             AS sample_count,
            MAX(d.unit)                          AS unit
        FROM daily_rollup AS d
        GROUP BY d.metric_type
    ),

    -- Build the ordered trend_points array (one entry per calendar day).
    daily_trends AS (
        SELECT
            d.metric_type,
            (ARRAY_AGG(d.daily_max ORDER BY d.record_date))[1:p_days] AS trend_points
        FROM daily_rollup AS d
        GROUP BY d.metric_type
    )

    SELECT
        mr.metric_type,
        mr.avg_value,
        mr.min_value,
        mr.max_value,
        -- latest_value: most recent raw reading within the strict window.
        (
            SELECT wv2.value
            FROM wearable_vitals AS wv2
            WHERE wv2.user_id     = p_user_id
              AND wv2.metric_type   = mr.metric_type
              AND wv2.recorded_at  >= NOW() - INTERVAL '1 day' * p_days
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
FIX-STEPS-AVG (023): daily_rollup uses MAX(value) per calendar day so stale
  partial step counts are trumped by the latest full-day total.
  metric_rollup is now computed from daily MAX values, giving:
    avg_value = average of daily totals (typical daily steps)
    min_value = lowest  daily total     (least active day)
    max_value = highest daily total     (most active day)
FIX-DEEP-SLEEP (023): MAX in daily_rollup also means stale zeros written by
  old code are overridden by the real deep-sleep value for that day.
FIX-TZ  (022): daily buckets use DATE(recorded_at AT TIME ZONE p_timezone).
FIX-C   (021): trend_points sliced to p_days entries.
FIX-D   (021): raw window +1 day for timezone-edge records.';

GRANT EXECUTE ON FUNCTION get_vitals_summary(UUID, INTEGER, TEXT)
TO anon, authenticated, service_role;
