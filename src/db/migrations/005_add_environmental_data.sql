-- Migration 005: Environmental Data Cache Table
-- Stores snapshots fetched from Open-Meteo (geocoding + forecast + AQI) so
-- the same city is not re-fetched on every single RAG query.
--
-- Apply this in your Supabase SQL editor AFTER migrations 001–004.

-- ── 1. Enable uuid-ossp extension (safe no-op if already active) ─────────────

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── 2. Create environmental_data table ───────────────────────────────────────

CREATE TABLE IF NOT EXISTS environmental_data (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID        REFERENCES auth.users(id) ON DELETE CASCADE,
    location_city   TEXT        NOT NULL,
    latitude        NUMERIC,                     -- degrees N, from geocoding API
    longitude       NUMERIC,                     -- degrees E, from geocoding API
    temperature_celsius  NUMERIC,
    humidity_percent     NUMERIC,
    aqi_level       INTEGER,                     -- US AQI 0–500 scale
    weather_condition    TEXT,                   -- human-readable, e.g. "Clear sky"
    weather_code    INTEGER,                     -- raw WMO weather code from Open-Meteo
    recorded_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE environmental_data IS
'Cached Open-Meteo weather + AQI snapshots.  One row per (user, fetch).  '
'Indexed by user + time so the most recent snapshot can be retrieved cheaply.';

COMMENT ON COLUMN environmental_data.weather_code IS
'WMO weather interpretation code returned by the Open-Meteo forecast API.  '
'See https://open-meteo.com/en/docs for the full code table.';

COMMENT ON COLUMN environmental_data.aqi_level IS
'US AQI as returned by the Open-Meteo air-quality API.  '
'Scale: 0–50 Good, 51–100 Moderate, 101–150 Unhealthy for sensitive groups, '
'151–200 Unhealthy, 201–300 Very Unhealthy, 301–500 Hazardous.';

-- ── 3. Index: cheaply retrieve the latest snapshot per user ──────────────────

CREATE INDEX IF NOT EXISTS idx_env_user_time
    ON environmental_data (user_id, recorded_at DESC);

-- ── 4. Index: cheaply look up the latest snapshot for a given city ────────────
-- Useful for shared/public city caches in future without a user_id join.

CREATE INDEX IF NOT EXISTS idx_env_city_time
    ON environmental_data (location_city, recorded_at DESC);
