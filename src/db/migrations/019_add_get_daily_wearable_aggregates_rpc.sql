-- Migration 019: Daily wearable aggregates RPC for gap-filled LLM trend context
--
-- Creates a Supabase RPC that pivots EAV wearable_vitals rows into one row per
-- calendar date with daily aggregates for the metrics currently used by the
-- LLM temporal-trend pipeline.

CREATE OR REPLACE FUNCTION get_daily_wearable_aggregates(
    p_user_id UUID,
    p_days INTEGER DEFAULT 7
)
RETURNS TABLE (
    record_date DATE,
    hr_min INTEGER,
    hr_max INTEGER,
    hr_avg INTEGER,
    sleep_minutes INTEGER,
    spo2_avg INTEGER,
    steps_total INTEGER
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        DATE(wv.recorded_at) AS record_date,
        MIN(wv.value) FILTER (WHERE wv.metric_type = 'heart_rate')::INTEGER AS hr_min,
        MAX(wv.value) FILTER (WHERE wv.metric_type = 'heart_rate')::INTEGER AS hr_max,
        ROUND(AVG(wv.value) FILTER (WHERE wv.metric_type = 'heart_rate'))::INTEGER AS hr_avg,
        ROUND(SUM(wv.value) FILTER (WHERE wv.metric_type = 'sleep_minutes'))::INTEGER AS sleep_minutes,
        ROUND(AVG(wv.value) FILTER (WHERE wv.metric_type = 'spo2'))::INTEGER AS spo2_avg,
        ROUND(SUM(wv.value) FILTER (WHERE wv.metric_type = 'steps'))::INTEGER AS steps_total
    FROM wearable_vitals AS wv
    WHERE wv.user_id = p_user_id
      AND wv.recorded_at >= (CURRENT_DATE - (GREATEST(p_days, 1) - 1))::TIMESTAMP
      AND wv.recorded_at < (CURRENT_DATE + 1)::TIMESTAMP
    GROUP BY DATE(wv.recorded_at)
    ORDER BY record_date ASC;
$$;

COMMENT ON FUNCTION get_daily_wearable_aggregates IS
'Returns one row per calendar day for the last N days with pivoted wearable aggregates: '
'heart-rate min/max/avg, total sleep minutes, average SpO2, and total steps. '
'Used by the RAG pipeline to build gap-filled daily trend arrays for the LLM.';
