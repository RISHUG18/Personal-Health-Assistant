-- Migration 015: Privacy hardening for account deletion, RLS, and report storage paths
--
-- Safe to re-run. This migration:
-- 1. Persists storage paths so backend deletion can remove Supabase Storage objects
-- 2. Adds missing DELETE/self-service RLS coverage
-- 3. Adds RLS for user-scoped tables used by the backend
--
-- This repo does not define every table locally, so this migration guards
-- each operation with existence checks to avoid failing on partially-managed
-- schemas.

CREATE EXTENSION IF NOT EXISTS pg_cron;

DO $migration$
BEGIN
    IF to_regclass('public.medical_reports') IS NOT NULL THEN
        EXECUTE 'ALTER TABLE public.medical_reports ADD COLUMN IF NOT EXISTS storage_path TEXT';
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_medical_reports_user_created ON public.medical_reports (user_id, created_at DESC)';
        EXECUTE $sql$
            COMMENT ON COLUMN public.medical_reports.storage_path IS
            'Supabase Storage object path for the uploaded report. Required for physical deletion during GDPR/DPDP erasure workflows.'
        $sql$;
    END IF;

    IF to_regclass('public.structured_reports') IS NOT NULL THEN
        EXECUTE 'ALTER TABLE public.structured_reports ADD COLUMN IF NOT EXISTS storage_path TEXT';
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_structured_reports_user_created ON public.structured_reports (user_id, created_at DESC)';
        EXECUTE $sql$
            COMMENT ON COLUMN public.structured_reports.storage_path IS
            'Supabase Storage object path for the uploaded structured report. Required for physical deletion during GDPR/DPDP erasure workflows.'
        $sql$;
    END IF;
END
$migration$;

ALTER TABLE IF EXISTS public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.doctor_patient_mapping ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.structured_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.medical_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.lab_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.wearable_vitals ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.environmental_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.alert_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.health_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.report_chunks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can delete their own profile" ON public.users;
CREATE POLICY "Users can delete their own profile"
    ON public.users FOR DELETE
    USING (auth.uid() = id);

DO $migration$
BEGIN
    IF to_regclass('public.doctor_patient_mapping') IS NOT NULL THEN
        EXECUTE 'DROP POLICY IF EXISTS "Doctors can view mapped patients profiles" ON public.users';
        EXECUTE $sql$
            CREATE POLICY "Doctors can view mapped patients profiles"
                ON public.users FOR SELECT
                USING (
                    EXISTS (
                        SELECT 1
                        FROM public.doctor_patient_mapping dpm
                        WHERE dpm.doctor_id = auth.uid()
                          AND dpm.patient_id = users.id
                    )
                )
        $sql$;
    END IF;

    IF to_regclass('public.doctor_patient_mapping') IS NOT NULL THEN
        EXECUTE 'DROP POLICY IF EXISTS "Doctors can manage their patient mappings" ON public.doctor_patient_mapping';
        EXECUTE $sql$
            CREATE POLICY "Doctors can manage their patient mappings"
                ON public.doctor_patient_mapping FOR ALL
                USING (doctor_id = auth.uid())
                WITH CHECK (doctor_id = auth.uid())
        $sql$;
    END IF;

    IF to_regclass('public.medical_reports') IS NOT NULL THEN
        EXECUTE 'DROP POLICY IF EXISTS "Users can manage their own medical_reports" ON public.medical_reports';
        EXECUTE $sql$
            CREATE POLICY "Users can manage their own medical_reports"
                ON public.medical_reports FOR ALL
                USING (auth.uid() = user_id)
                WITH CHECK (auth.uid() = user_id)
        $sql$;

        EXECUTE 'DROP POLICY IF EXISTS "Doctors can view mapped patients medical_reports" ON public.medical_reports';
        EXECUTE $sql$
            CREATE POLICY "Doctors can view mapped patients medical_reports"
                ON public.medical_reports FOR SELECT
                USING (
                    EXISTS (
                        SELECT 1
                        FROM public.doctor_patient_mapping dpm
                        WHERE dpm.doctor_id = auth.uid()
                          AND dpm.patient_id = medical_reports.user_id
                    )
                )
        $sql$;
    END IF;

    IF to_regclass('public.structured_reports') IS NOT NULL THEN
        EXECUTE 'DROP POLICY IF EXISTS "Users can manage their own structured_reports" ON public.structured_reports';
        EXECUTE $sql$
            CREATE POLICY "Users can manage their own structured_reports"
                ON public.structured_reports FOR ALL
                USING (auth.uid() = user_id)
                WITH CHECK (auth.uid() = user_id)
        $sql$;

        EXECUTE 'DROP POLICY IF EXISTS "Doctors can view mapped patients structured_reports" ON public.structured_reports';
        EXECUTE $sql$
            CREATE POLICY "Doctors can view mapped patients structured_reports"
                ON public.structured_reports FOR SELECT
                USING (
                    EXISTS (
                        SELECT 1
                        FROM public.doctor_patient_mapping dpm
                        WHERE dpm.doctor_id = auth.uid()
                          AND dpm.patient_id = structured_reports.user_id
                    )
                )
        $sql$;
    END IF;

    IF to_regclass('public.lab_results') IS NOT NULL AND to_regclass('public.medical_reports') IS NOT NULL THEN
        EXECUTE 'DROP POLICY IF EXISTS "Users can view their own lab_results" ON public.lab_results';
        EXECUTE $sql$
            CREATE POLICY "Users can view their own lab_results"
                ON public.lab_results FOR SELECT
                USING (
                    EXISTS (
                        SELECT 1
                        FROM public.medical_reports mr
                        WHERE mr.id = lab_results.report_id
                          AND mr.user_id = auth.uid()
                    )
                )
        $sql$;

        EXECUTE 'DROP POLICY IF EXISTS "Doctors can view mapped patients lab_results" ON public.lab_results';
        EXECUTE $sql$
            CREATE POLICY "Doctors can view mapped patients lab_results"
                ON public.lab_results FOR SELECT
                USING (
                    EXISTS (
                        SELECT 1
                        FROM public.medical_reports mr
                        JOIN public.doctor_patient_mapping dpm
                          ON dpm.patient_id = mr.user_id
                        WHERE mr.id = lab_results.report_id
                          AND dpm.doctor_id = auth.uid()
                    )
                )
        $sql$;
    END IF;

    IF to_regclass('public.report_chunks') IS NOT NULL THEN
        EXECUTE 'DROP POLICY IF EXISTS "Users can view their own report_chunks" ON public.report_chunks';
        EXECUTE $sql$
            CREATE POLICY "Users can view their own report_chunks"
                ON public.report_chunks FOR SELECT
                USING (auth.uid() = user_id)
        $sql$;
    END IF;

    IF to_regclass('public.wearable_vitals') IS NOT NULL THEN
        EXECUTE 'DROP POLICY IF EXISTS "Users can manage their own wearable_vitals" ON public.wearable_vitals';
        EXECUTE $sql$
            CREATE POLICY "Users can manage their own wearable_vitals"
                ON public.wearable_vitals FOR ALL
                USING (auth.uid() = user_id)
                WITH CHECK (auth.uid() = user_id)
        $sql$;
    END IF;

    IF to_regclass('public.environmental_data') IS NOT NULL THEN
        EXECUTE 'DROP POLICY IF EXISTS "Users can manage their own environmental_data" ON public.environmental_data';
        EXECUTE $sql$
            CREATE POLICY "Users can manage their own environmental_data"
                ON public.environmental_data FOR ALL
                USING (auth.uid() = user_id)
                WITH CHECK (auth.uid() = user_id)
        $sql$;
    END IF;

    IF to_regclass('public.alerts') IS NOT NULL THEN
        EXECUTE 'DROP POLICY IF EXISTS "Users can view their own alerts" ON public.alerts';
        EXECUTE $sql$
            CREATE POLICY "Users can view their own alerts"
                ON public.alerts FOR SELECT
                USING (auth.uid() = user_id)
        $sql$;

        EXECUTE 'DROP POLICY IF EXISTS "Doctors can view mapped patients alerts" ON public.alerts';
        EXECUTE $sql$
            CREATE POLICY "Doctors can view mapped patients alerts"
                ON public.alerts FOR SELECT
                USING (
                    EXISTS (
                        SELECT 1
                        FROM public.doctor_patient_mapping dpm
                        WHERE dpm.doctor_id = auth.uid()
                          AND dpm.patient_id = alerts.user_id
                    )
                )
        $sql$;
    END IF;

    IF to_regclass('public.alert_evidence') IS NOT NULL AND to_regclass('public.alerts') IS NOT NULL THEN
        EXECUTE 'DROP POLICY IF EXISTS "Users can view their own alert evidence" ON public.alert_evidence';
        EXECUTE $sql$
            CREATE POLICY "Users can view their own alert evidence"
                ON public.alert_evidence FOR SELECT
                USING (
                    EXISTS (
                        SELECT 1
                        FROM public.alerts a
                        WHERE a.id = alert_evidence.alert_id
                          AND a.user_id = auth.uid()
                    )
                )
        $sql$;

        EXECUTE 'DROP POLICY IF EXISTS "Doctors can view mapped patients alert evidence" ON public.alert_evidence';
        EXECUTE $sql$
            CREATE POLICY "Doctors can view mapped patients alert evidence"
                ON public.alert_evidence FOR SELECT
                USING (
                    EXISTS (
                        SELECT 1
                        FROM public.alerts a
                        JOIN public.doctor_patient_mapping dpm
                          ON dpm.patient_id = a.user_id
                        WHERE a.id = alert_evidence.alert_id
                          AND dpm.doctor_id = auth.uid()
                    )
                )
        $sql$;
    END IF;

    IF to_regclass('public.health_summaries') IS NOT NULL THEN
        EXECUTE 'DROP POLICY IF EXISTS "Patients can view own user summaries" ON public.health_summaries';
        EXECUTE $sql$
            CREATE POLICY "Patients can view own user summaries"
                ON public.health_summaries FOR SELECT
                USING (
                    auth.uid() = user_id
                    AND target_role = 'user'
                )
        $sql$;

        EXECUTE 'DROP POLICY IF EXISTS "Doctors can view patient doctor summaries" ON public.health_summaries';
        EXECUTE $sql$
            CREATE POLICY "Doctors can view patient doctor summaries"
                ON public.health_summaries FOR SELECT
                USING (
                    target_role = 'doctor'
                    AND EXISTS (
                        SELECT 1
                        FROM public.doctor_patient_mapping dpm
                        WHERE dpm.doctor_id = auth.uid()
                          AND dpm.patient_id = health_summaries.user_id
                    )
                )
        $sql$;

        EXECUTE 'DROP POLICY IF EXISTS "Service role can insert summaries" ON public.health_summaries';
        EXECUTE $sql$
            CREATE POLICY "Service role can insert summaries"
                ON public.health_summaries FOR INSERT
                WITH CHECK (true)
        $sql$;

        EXECUTE $sql$
            COMMENT ON TABLE public.health_summaries IS
            'AI-generated summaries retained for 1 year by default. Raw report/PDF retention that requires Storage deletion must be enforced by the backend service, not by SQL alone.'
        $sql$;
    END IF;
END
$migration$;

DO $migration$
BEGIN
    IF to_regclass('public.health_summaries') IS NOT NULL
       AND EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron')
       AND NOT EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'purge-stale-health-summaries')
    THEN
        PERFORM cron.schedule(
            'purge-stale-health-summaries',
            '0 5 * * 0',
            $$DELETE FROM public.health_summaries
              WHERE created_at < NOW() - INTERVAL '1 year'$$
        );
    END IF;
END
$migration$;
