-- Migration 006: Wearable Vitals Time-Series Table
-- Stores high-frequency continuous data from fitness bands and wearable devices.
-- Optimized for time-series queries (last N days aggregation).
--
-- ── 1. Enable uuid-ossp extension (safe no-op if already active) ─────────────

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── 2. Create wearable_vitals table ──────────────────────────────────────────
-- Design: EAV (Entity-Attribute-Value) pattern with metric_type column.
-- Allows storing heterogeneous metrics (sleep, heart_rate, steps) in one table
-- without schema changes when new metric types are added.

CREATE TABLE IF NOT EXISTS wearable_vitals (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID        NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    recorded_at     TIMESTAMP WITH TIME ZONE NOT NULL,
    metric_type     TEXT        NOT NULL,
    value           NUMERIC     NOT NULL,
    unit            TEXT,                       -- e.g., 'bpm', 'steps', 'minutes', 'hours'
    device_id       TEXT,                       -- optional device identifier
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Prevent duplicate readings for the same (user, timestamp, metric)
    CONSTRAINT unique_user_metric_time UNIQUE (user_id, recorded_at, metric_type)
);

COMMENT ON TABLE wearable_vitals IS
'Time-series table for high-frequency wearable device metrics.  '
'EAV pattern: each row is one (timestamp, metric_type, value) tuple.  '
'Indexed for efficient 7-day aggregation queries by user and metric type.';

COMMENT ON COLUMN wearable_vitals.metric_type IS
'Type of vital metric being recorded.  Standard values:  '
'heart_rate (bpm), steps (count), sleep_minutes (min), deep_sleep_minutes (min), '
'calories_burned (kcal), active_minutes (min), spo2 (%), hrv_ms (ms), '
'resting_heart_rate (bpm), sleep_score (0-100).';

COMMENT ON COLUMN wearable_vitals.recorded_at IS
'Timestamp when the metric was actually measured by the device, not when it was ingested.';

COMMENT ON COLUMN wearable_vitals.device_id IS
'Optional identifier for the source device (e.g., "fitbit_xyz", "garmin_abc").  '
'Useful for users with multiple wearables.';

-- ── 3. Indexes for efficient time-range queries ──────────────────────────────

-- Primary query pattern: fetch last 7 days of vitals for a user
CREATE INDEX IF NOT EXISTS idx_vitals_user_time
    ON wearable_vitals (user_id, recorded_at DESC);

-- Secondary pattern: fetch specific metric type for a user over time
CREATE INDEX IF NOT EXISTS idx_vitals_user_metric_time
    ON wearable_vitals (user_id, metric_type, recorded_at DESC);

-- ── 4. Partitioning hint (for future high-volume deployments) ────────────────
-- If data volume grows significantly, consider range-partitioning by recorded_at
-- (e.g., monthly partitions).  For MVP scale, standard indexes suffice.

-- ── 5. RPC function for 7-day aggregation ────────────────────────────────────
-- Returns aggregated vitals for the context builder.

CREATE OR REPLACE FUNCTION get_vitals_summary(
    p_user_id UUID,
    p_days INTEGER DEFAULT 7
)
RETURNS TABLE (
    metric_type TEXT,
    avg_value NUMERIC,
    min_value NUMERIC,
    max_value NUMERIC,
    latest_value NUMERIC,
    sample_count BIGINT,
    unit TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT
        wv.metric_type,
        ROUND(AVG(wv.value)::NUMERIC, 2) AS avg_value,
        MIN(wv.value) AS min_value,
        MAX(wv.value) AS max_value,
        (
            SELECT wv2.value
            FROM wearable_vitals wv2
            WHERE wv2.user_id = p_user_id
              AND wv2.metric_type = wv.metric_type
            ORDER BY wv2.recorded_at DESC
            LIMIT 1
        ) AS latest_value,
        COUNT(*) AS sample_count,
        MAX(wv.unit) AS unit
    FROM wearable_vitals wv
    WHERE wv.user_id = p_user_id
      AND wv.recorded_at >= NOW() - (p_days || ' days')::INTERVAL
    GROUP BY wv.metric_type
    ORDER BY wv.metric_type;
END;
$$;

COMMENT ON FUNCTION get_vitals_summary IS
'Returns aggregated vitals (avg, min, max, latest, count) for the last N days.  '
'Used by the Context Builder V2 to prepare wearable data for Gemini prompts.';
