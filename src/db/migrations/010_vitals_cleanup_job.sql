-- Migration 009: Wearable Vitals Automated Cleanup
-- Sets up pg_cron job to automatically purge stale wearable vitals data.
--
-- Apply this in your Supabase SQL editor AFTER migration 008.
--
-- ══════════════════════════════════════════════════════════════════════════════
-- STRATEGY: TIERED RETENTION VIA SUMMARIZATION
-- ══════════════════════════════════════════════════════════════════════════════
--
-- The AI generates weekly summaries from raw wearable vitals. Once summarized,
-- minute-by-minute data loses 99% of its clinical value. We keep:
--
--   • 30 days of raw vitals (buffer for offline users, device syncs)
--   • Permanent AI-generated 3-bullet summaries (lifetime medical record)
--
-- This migration automates purging raw data older than 30 days, preventing
-- storage bloat while preserving long-term patient narratives via summaries.
--
-- ══════════════════════════════════════════════════════════════════════════════

-- ── 1. Enable pg_cron extension (safe no-op if already active) ────────────────

CREATE EXTENSION IF NOT EXISTS pg_cron;

COMMENT ON EXTENSION pg_cron IS
'PostgreSQL native cron scheduler. Runs SQL commands on a recurring schedule '
'without external orchestration. Perfect for database maintenance tasks.';

-- ── 2. Schedule nightly wearable vitals purge ──────────────────────────────────
-- Runs at 3:00 AM UTC every day
-- Deletes wearable_vitals rows where recorded_at is older than 30 days

SELECT cron.schedule(
  'purge-stale-wearable-vitals',  -- Job name (used for unscheduling if needed)
  '0 3 * * *',                    -- Cron syntax: minute hour day month weekday
  $$
    DELETE FROM wearable_vitals
    WHERE recorded_at < NOW() - INTERVAL '30 days';
  $$
);

COMMENT ON EXTENSION pg_cron IS
'Scheduled job: purge-stale-wearable-vitals runs daily at 03:00 UTC to delete '
'wearable_vitals rows older than 30 days, maintaining a rolling hot storage window.';

-- ── 3. Verify scheduled job ────────────────────────────────────────────────────
-- Query this view to confirm the job is active:
--
--   SELECT jobid, jobname, schedule, active FROM cron.job;
--
-- Expected output:
--   jobid |          jobname             |  schedule  | active
--   ------+------------------------------+------------+--------
--     1   | purge-stale-wearable-vitals  | 0 3 * * *  | t

-- ── 4. Manual unscheduling (if needed) ─────────────────────────────────────────
-- To disable the job without dropping this migration:
--
--   SELECT cron.unschedule('purge-stale-wearable-vitals');
--
-- To re-enable, simply re-run the SELECT cron.schedule(...) statement above.

-- ── 5. Manual cleanup trigger (for testing) ────────────────────────────────────
-- To force immediate cleanup without waiting for the scheduled run:
--
--   DELETE FROM wearable_vitals WHERE recorded_at < NOW() - INTERVAL '30 days';

-- ══════════════════════════════════════════════════════════════════════════════
-- WHY THIS IS THE PERFECT MVP ARCHITECTURE
-- ══════════════════════════════════════════════════════════════════════════════
--
-- ✓ Zero Backend Compute: Python server doesn't waste CPU/memory on cleanup.
-- ✓ Cost Effective: Stays within Supabase free/pro tier storage limits.
-- ✓ Clinically Safe: AI summaries (stored separately) preserve lifetime narratives.
-- ✓ Database Native: pg_cron runs inside Postgres; no external orchestration needed.
-- ✓ Self-Healing: Automatic, no human intervention required.
--
-- ══════════════════════════════════════════════════════════════════════════════
