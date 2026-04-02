# Golden Path Database Seeding - Production Demo Scenario

**Date**: April 3, 2026  
**Purpose**: Seed production database with the ideal end-to-end user journey  
**Duration**: 12 hours of simulated timeline (09:00 - 21:00)

---

## Scenario Overview: "Riya's Health Journey"

### The Story
Riya, a 34-year-old with a family history of anemia, uploads an old blood test report online. Her wearable device syncs continuously, detecting high heart rate patterns and poor sleep. The system correlates these signals with her lab results and environmental stressors (heat wave), triggering a HIGH-priority alert. Dr. Priya, her assigned physician, reviews the alert and acknowledges it with clinical recommendations. When Riya asks "Why did I get an alert?", the AI system provides a grounded, personalized explanation citing all evidence.

### Key Narrative Arc
```
09:00 - Patient Registration & Consent
   ↓
10:30 - Report Upload (OCR → Extraction)
   ↓
11:00 - Wearable Data Sync (7 days, 10k+ readings)
   ↓
12:00 - Rules Engine Evaluation (Hourly Cron)
   ↓
12:05 - Alert Generation (HIGH severity)
   ↓
14:30 - Doctor Reviews Dashboard (Patient #1 priority)
   ↓
14:35 - Alert Drill-Down & Evidence
   ↓
14:40 - Doctor Acknowledges & Adds Note
   ↓
18:00 - Patient Voice Query
   ↓
18:10 - AI Response (RAG-contextualized)
   ↓
21:00 - 14-day Follow-up Alert
```

---

## SQL Seeding Script

**Environment**: PostgreSQL (Supabase)  
**Schema**: See `src/backend/models/schemas.py` for table definitions

### Execute These Statements (In Order)

#### Step 1: Create Users

```sql
-- User 1: Patient (Riya Kumar)
INSERT INTO public.users (
    id, email, full_name, role, status, phone, date_of_birth,
    gender, medical_conditions, allergies, emergency_contact,
    created_at, updated_at
) VALUES (
    'user_riya_001',
    'riya.kumar@example.com',
    'Riya Kumar',
    'patient',
    'active',
    '+91-9876543210',
    '1991-12-15',
    'Female',
    ARRAY['Anemia', 'Hypertension'],
    ARRAY['Penicillin'],
    '{"name": "Rajesh Kumar", "phone": "+91-9876543200"}',
    NOW(),
    NOW()
);

-- User 2: Doctor (Dr. Priya Sharma)
INSERT INTO public.users (
    id, email, full_name, role, status, phone, specialization,
    license_number, hospital_id, created_at, updated_at
) VALUES (
    'user_doc_priya_001',
    'priya@hospital.local',
    'Dr. Priya Sharma',
    'doctor',
    'active',
    '+91-9123456789',
    'Internal Medicine',
    'MCI2024001234',
    'hosp_001',
    NOW(),
    NOW()
);
```

#### Step 2: Create Consent Records (Patient → Doctor)

```sql
INSERT INTO public.consent_records (
    id, patient_id, doctor_id, scope, status, 
    created_at, expires_at, acknowledged_date
) VALUES (
    'consent_001',
    'user_riya_001',
    'user_doc_priya_001',
    ARRAY['view_reports', 'view_vitals', 'view_alerts', 'view_demographics'],
    'active',
    NOW(),
    NOW() + INTERVAL '1 year',
    NOW()
);

-- Wearable data consent
INSERT INTO public.consent_records (
    id, patient_id, doctor_id, scope, status,
    created_at, expires_at, acknowledged_date
) VALUES (
    'consent_002',
    'user_riya_001',
    'user_doc_priya_001',
    ARRAY['view_wearable_data', 'sync_wearable'],
    'active',
    NOW(),
    NOW() + INTERVAL '1 year',
    NOW()
);
```

#### Step 3: Upload Medical Report (CBC - Complete Blood Count)

```sql
-- Report Record
INSERT INTO public.medical_reports (
    id, patient_id, doctor_id, report_type, file_name,
    upload_date, report_date, extraction_status,
    ocr_confidence, created_at
) VALUES (
    'report_cbc_001',
    'user_riya_001',
    'user_doc_priya_001',
    'CBC',
    'CBC_Jan2026.pdf',
    NOW() - INTERVAL '2 hours',  -- 10:30 simulation time
    '2026-01-15',
    'extracted',
    0.94,
    NOW() - INTERVAL '2 hours'
);

-- Extracted Lab Values from CBC
INSERT INTO public.lab_values (
    id, report_id, test_name, test_code, value, 
    unit, reference_min, reference_max, status, created_at
) VALUES
    ('lab_001', 'report_cbc_001', 'Hemoglobin', 'HB', 9.8, 'g/dL', 12.0, 17.5, 'LOW', NOW()),
    ('lab_002', 'report_cbc_001', 'Hematocrit', 'HCT', 29.4, '%', 36.0, 50.0, 'LOW', NOW()),
    ('lab_003', 'report_cbc_001', 'Red Cell Count', 'RBC', 3.1, 'M/µL', 4.0, 5.5, 'LOW', NOW()),
    ('lab_004', 'report_cbc_001', 'Serum Iron', 'SI', 42, 'µg/dL', 60, 170, 'LOW', NOW()),
    ('lab_005', 'report_cbc_001', 'WBC Count', 'WBC', 7.2, 'K/µL', 4.5, 11.0, 'NORMAL', NOW()),
    ('lab_006', 'report_cbc_001', 'Platelets', 'PLT', 245, 'K/µL', 150, 400, 'NORMAL', NOW());

-- AI-Generated Insights
INSERT INTO public.report_insights (
    id, report_id, insight_type, confidence_score, 
    summary, detailed_analysis, recommendations
) VALUES (
    'insight_cbc_001',
    'report_cbc_001',
    'anemia_risk',
    0.92,
    'Patient shows signs of iron-deficiency anemia',
    'Hemoglobin (9.8 g/dL) and serum iron (42 µg/dL) are both below normal ranges. Hematocrit at 29.4% indicates mild anemia. Pattern consistent with iron deficiency.',
    ARRAY[
        'Increase dietary iron intake (red meat, spinach, fortified cereals)',
        'Consider iron supplementation (18-27 mg/day)',
        'Recheck CBC in 4 weeks',
        'Screen for GI blood loss if no improvement'
    ]
);
```

#### Step 4: Sync Wearable Device Data (Apple Watch)

```sql
-- 7 days × 1440 minutes = 10,080 heart rate readings
-- We'll seed 3 composite records representing daily summaries + peak anomalies

-- Day 1: March 28, 2026 (Normal)
INSERT INTO public.wearable_vitals (
    id, patient_id, device_type, metric_type, value, 
    unit, reading_timestamp, recording_quality
) VALUES
    ('vital_001', 'user_riya_001', 'apple_watch', 'heart_rate', 68, 'bpm', NOW() - INTERVAL '7 days' + INTERVAL '08:00', 0.98),
    ('vital_002', 'user_riya_001', 'apple_watch', 'heart_rate', 72, 'bpm', NOW() - INTERVAL '7 days' + INTERVAL '12:00', 0.97),
    ('vital_003', 'user_riya_001', 'apple_watch', 'heart_rate', 65, 'bpm', NOW() - INTERVAL '7 days' + INTERVAL '20:00', 0.96),
    ('vital_004', 'user_riya_001', 'apple_watch', 'sleep_duration', 7.5, 'hours', NOW() - INTERVAL '7 days' + INTERVAL '06:00', 0.95),
    ('vital_005', 'user_riya_001', 'apple_watch', 'sleep_quality', 'good', 'categorical', NOW() - INTERVAL '7 days' + INTERVAL '06:00', 0.92);

-- Day 3-4: March 30-31 (Heat wave begins - anomaly)
INSERT INTO public.wearable_vitals (
    id, patient_id, device_type, metric_type, value,
    unit, reading_timestamp, recording_quality
) VALUES
    ('vital_006', 'user_riya_001', 'apple_watch', 'heart_rate', 85, 'bpm', NOW() - INTERVAL '5 days' + INTERVAL '14:00', 0.96),
    ('vital_007', 'user_riya_001', 'apple_watch', 'heart_rate', 92, 'bpm', NOW() - INTERVAL '5 days' + INTERVAL '16:00', 0.94),  -- SPIKE
    ('vital_008', 'user_riya_001', 'apple_watch', 'heart_rate', 88, 'bpm', NOW() - INTERVAL '5 days' + INTERVAL '18:00', 0.95),
    ('vital_009', 'user_riya_001', 'apple_watch', 'sleep_duration', 5.2, 'hours', NOW() - INTERVAL '5 days' + INTERVAL '06:00', 0.91),  -- POOR SLEEP
    ('vital_010', 'user_riya_001', 'apple_watch', 'sleep_quality', 'poor', 'categorical', NOW() - INTERVAL '5 days' + INTERVAL '06:00', 0.88);

-- Day 6: April 2 (Today - continued elevated HR pattern)
INSERT INTO public.wearable_vitals (
    id, patient_id, device_type, metric_type, value,
    unit, reading_timestamp, recording_quality
) VALUES
    ('vital_011', 'user_riya_001', 'apple_watch', 'heart_rate', 89, 'bpm', NOW() - INTERVAL '1 day' + INTERVAL '08:00', 0.97),
    ('vital_012', 'user_riya_001', 'apple_watch', 'heart_rate', 94, 'bpm', NOW() - INTERVAL '1 day' + INTERVAL '15:00', 0.95),  -- SPIKE CONTINUED
    ('vital_013', 'user_riya_001', 'apple_watch', 'sleep_duration', 4.8, 'hours', NOW() - INTERVAL '1 day' + INTERVAL '06:00', 0.89),  -- POOR SLEEP
    ('vital_014', 'user_riya_001', 'apple_watch', 'sleep_quality', 'poor', 'categorical', NOW() - INTERVAL '1 day' + INTERVAL '06:00', 0.87);

-- Aggregate Daily Vitals Summary
INSERT INTO public.vitals_summary (
    id, patient_id, summary_date, avg_heart_rate, max_heart_rate,
    min_heart_rate, avg_sleep_hours, sleep_quality_score, created_at
) VALUES
    ('summary_001', 'user_riya_001', (NOW() - INTERVAL '7 days')::date, 68, 75, 62, 7.5, 0.88, NOW()),
    ('summary_002', 'user_riya_001', (NOW() - INTERVAL '5 days')::date, 86, 92, 78, 5.2, 0.58, NOW()),
    ('summary_003', 'user_riya_001', (NOW() - INTERVAL '1 day')::date, 91, 94, 85, 4.8, 0.55, NOW());
```

#### Step 5: Environmental Context (AQI, Weather)

```sql
INSERT INTO public.environmental_data (
    id, patient_id, location, aqi_value, aqi_category,
    temperature_celsius, humidity_percent, 
    pollutants, recorded_at
) VALUES
    -- Normal week
    ('env_001', 'user_riya_001', 'Delhi, India', 68, 'Moderate', 28, 55, ARRAY['PM2.5:45', 'PM10:78'], NOW() - INTERVAL '7 days'),
    -- Heat wave period (AQI elevated to UNHEALTHY)
    ('env_002', 'user_riya_001', 'Delhi, India', 145, 'UNHEALTHY', 41, 25, ARRAY['PM2.5:185', 'PM10:312', 'O3:78'], NOW() - INTERVAL '5 days'),
    ('env_003', 'user_riya_001', 'Delhi, India', 142, 'UNHEALTHY', 42, 23, ARRAY['PM2.5:180', 'PM10:305', 'O3:82'], NOW() - INTERVAL '2 days'),
    ('env_004', 'user_riya_001', 'Delhi, India', 138, 'UNHEALTHY', 40, 26, ARRAY['PM2.5:165', 'PM10:290', 'O3:75'], NOW() - INTERVAL '1 day');
```

#### Step 6: Trigger Alert Generation Rules

```sql
-- Alert Rule Definitions (Pre-existing in system)
-- Rule 1: Low Hemoglobin + High HR Pattern + Poor AQI = HIGH Alert
INSERT INTO public.alert_rules (
    id, rule_name, priority_level, conditions,
    actions, created_by, is_active
) VALUES (
    'rule_001',
    'Anemia + Environmental Stress + Poor Sleep',
    'HIGH',
    JSONB_BUILD_OBJECT(
        'lab_condition', 'hemoglobin < 10.5',
        'vitals_condition', 'heart_rate > 85 for 3+ readings',
        'environmental_condition', 'AQI > 100 OR temperature > 38C',
        'sleep_condition', 'sleep_quality < 0.6 for 2+ nights'
    ),
    ARRAY['generate_alert', 'notify_doctor', 'notify_patient'],
    'system_admin',
    TRUE
);

-- Generated Alert (Fired by cron job at 12:05)
INSERT INTO public.alerts (
    id, patient_id, doctor_id, alert_type, priority,
    status, triggered_by_rule, evidence, 
    created_at, acknowledged_at, acknowledged_by
) VALUES (
    'alert_001',
    'user_riya_001',
    'user_doc_priya_001',
    'HEALTH_RISK',
    'HIGH',
    'acknowledged',
    'rule_001',
    JSONB_BUILD_OBJECT(
        'findings', ARRAY[
            'Hemoglobin: 9.8 g/dL (LOW)',
            'Heart Rate Pattern: 85-94 bpm consistently elevated',
            'Sleep Quality: Poor for 3 consecutive nights',
            'AQI: 145 (UNHEALTHY) - High particulate matter',
            'Temperature: 40-42°C (Heat wave)'
        ],
        'risk_level', 'MEDIUM_HIGH',
        'interpretation', 'Patient with iron-deficiency anemia + elevated stress response + environmental heat exposure = increased infection/complications risk',
        'evidence_timeline', JSONB_BUILD_ARRAY(
            JSONB_BUILD_OBJECT('timestamp', '2026-01-15', 'event', 'Report uploaded: Hb 9.8 g/dL'),
            JSONB_BUILD_OBJECT('timestamp', '2026-03-28', 'event', 'Wearable sync started'),
            JSONB_BUILD_OBJECT('timestamp', '2026-03-30', 'event', 'Heat wave begins, HR spikes to 92 bpm'),
            JSONB_BUILD_OBJECT('timestamp', '2026-03-31', 'event', 'Poor sleep (5.2 hrs), AQI reaches 145'),
            JSONB_BUILD_OBJECT('timestamp', '2026-04-02', 'event', 'Pattern continues - triggered alert rule'),
            JSONB_BUILD_OBJECT('timestamp', NOW(), 'event', 'Alert prioritized for Dr. Priya')
        )
    ),
    NOW() - INTERVAL '4 hours',  -- Alert created at 12:05
    NOW() - INTERVAL '3 hours',  -- Acknowledged at 14:35
    'user_doc_priya_001'
);

-- Alert Notification Record
INSERT INTO public.alert_notifications (
    id, alert_id, recipient_id, channel, status,
    sent_at, delivered_at
) VALUES
    ('notif_001', 'alert_001', 'user_doc_priya_001', 'email', 'delivered', NOW() - INTERVAL '4 hours', NOW() - INTERVAL '3 hours 50 minutes'),
    ('notif_002', 'alert_001', 'user_doc_priya_001', 'push', 'delivered', NOW() - INTERVAL '4 hours', NOW() - INTERVAL '3 hours 55 minutes'),
    ('notif_003', 'alert_001', 'user_riya_001', 'email', 'delivered', NOW() - INTERVAL '4 hours', NOW() - INTERVAL '3 hours 50 minutes');
```

#### Step 7: Doctor's Clinical Acknowledgement

```sql
-- Doctor views patient detail and adds clinical note
INSERT INTO public.clinical_notes (
    id, alert_id, patient_id, doctor_id, note_type,
    content, recommendations, follow_up_date, created_at
) VALUES (
    'note_001',
    'alert_001',
    'user_riya_001',
    'user_doc_priya_001',
    'alert_response',
    'Patient presenting with signs of iron-deficiency anemia (Hb 9.8 g/dL). Elevated heart rate pattern correlates with environmental stress (42°C heat wave, AQI 145) and poor sleep quality. Combined effect increases risk of infection and cardiovascular strain.',
    ARRAY[
        'Start ferrous sulfate 325mg daily with orange juice',
        'Increase water intake to 3-4L daily during heatwave',
        'Avoid prolonged outdoor exposure during peak hours (12-4 PM)',
        'Maintain consistent sleep schedule',
        'Recheck CBC in 2 weeks',
        'Daily vital monitoring via wearable device'
    ],
    NOW() + INTERVAL '14 days',
    NOW() - INTERVAL '3 hours'
);

-- Update alert with acknowledgement status
UPDATE public.alerts 
SET status = 'acknowledged', 
    acknowledged_at = NOW() - INTERVAL '3 hours',
    acknowledged_by = 'user_doc_priya_001'
WHERE id = 'alert_001';
```

#### Step 8: Patient Voice Query (RAG Context)

```sql
-- Store voice interaction for retrieval-augmented generation (RAG)
INSERT INTO public.voice_queries (
    id, patient_id, question, question_embedding,
    created_at
) VALUES (
    'query_001',
    'user_riya_001',
    'Why did I get an alert?',
    '[0.12, 0.45, 0.67, ...]'::vector,  -- Actual embeddings from Gemini
    NOW() - INTERVAL '2 hours'  -- 18:00 simulation
);

-- AI Voice Response (Generated by RAG system querying above context)
INSERT INTO public.voice_responses (
    id, query_id, patient_id, model, response_text,
    confidence_score, sources_used, generated_at
) VALUES (
    'response_001',
    'query_001',
    'user_riya_001',
    'gemini-2.5-pro',
    'You received a HIGH priority alert because three factors combined: First, your blood test from January showed low hemoglobin at 9.8, indicating anemia. Second, your watch detected elevated heart rates of 85 to 94 beats per minute over the past few days, and poor sleep patterns. Third, Delhi is experiencing a heat wave with very poor air quality - AQI at 145. When anemia combines with stress response and environmental pollution, it puts extra strain on your heart and immune system. Dr. Priya has recommended iron supplements and recommended you stay indoors during peak heat hours. Please follow her advice and we''ll recheck your blood in two weeks.',
    0.94,
    ARRAY[
        'report_cbc_001',
        'summary_002',
        'summary_003',
        'env_002',
        'env_003',
        'env_004',
        'alert_001',
        'clinical_notes.note_001'
    ],
    NOW() - INTERVAL '2 hours'
);
```

#### Step 9: Schedule Follow-up Alert (14-day check-in)

```sql
INSERT INTO public.scheduled_tasks (
    id, patient_id, task_type, trigger_date,
    description, status, created_at
) VALUES (
    'task_001',
    'user_riya_001',
    'remind_recheck_labs',
    NOW() + INTERVAL '14 days',
    'Time to recheck CBC as recommended by Dr. Priya. Hemoglobin should improve with iron supplementation.',
    'scheduled',
    NOW()
);
```

---

## Dashboard Views After Seeding

### Patient Dashboard (After Seeding)

**Riya's Home Screen** shows:
- 🔴 **1 HIGH Alert**: "Elevated infection risk due to anemia + environmental stress"
- 📊 **Key Metrics**: 
  - Hemoglobin: 9.8 g/dL (LOW - red indicator)
  - Last 7-day avg HR: 86 bpm (elevated, yellow indicator)
  - Last night sleep: 4.8 hours (poor, red indicator)
  - Current AQI: 138 (UNHEALTHY, red indicator)
- 📅 **Upcoming**: Lab recheck in 14 days
- 🩺 **Dr. Priya's Note**: Iron supplementation recommended

### Doctor Dashboard (After Seeding)

**Dr. Priya's Patient List** shows:
1. ⭐ **#1 - Riya Kumar** (HIGH Alert)
   - Status: Alert acknowledged by you on Apr 3, 14:35
   - Latest: Hemoglobin low, environmental stress factor
   - Action: Follow-up in 14 days

**Clicking into Riya's Detail View**:
- Alert Summary: "Anemia + Heat stress + Poor sleep = high risk"
- Timeline:
  - Jan 15: CBC uploaded (Hb 9.8)
  - Mar 28-Apr 2: Elevated HR pattern, poor sleep
  - Mar 30: AQI spike to 145
  - Apr 3 12:05: Alert triggered
- Lab Values: Interactive chart showing Hb, iron, RBC trends
- Wearable Data: HR graph showing spikes, sleep bar chart
- Environmental: Temperature and AQI timeline
- Your Notes: Iron supplementation started

---

## Verification Checklist

After executing all SQL:

- [ ] **Users Created**: 1 patient (Riya), 1 doctor (Dr. Priya)
- [ ] **Consent Records**: 2 records linking patient ↔ doctor
- [ ] **Medical Report**: CBC with 6 lab values extracted
- [ ] **Wearable Data**: 14 vital readings (HR, sleep) + 3 daily summaries
- [ ] **Environmental Data**: 4 AQI records showing progression
- [ ] **Alert Generated**: 1 HIGH priority alert with full evidence trail
- [ ] **Clinical Note**: Doctor's response with recommendations
- [ ] **Voice Query**: Patient question stored with AI response
- [ ] **Follow-up Task**: 14-day recheck scheduled

**Data Integrity Checks**:
```sql
-- Count seeded records
SELECT 
    (SELECT COUNT(*) FROM users WHERE role = 'patient') as patients,
    (SELECT COUNT(*) FROM users WHERE role = 'doctor') as doctors,
    (SELECT COUNT(*) FROM consent_records) as consents,
    (SELECT COUNT(*) FROM lab_values) as lab_values,
    (SELECT COUNT(*) FROM wearable_vitals) as vitals,
    (SELECT COUNT(*) FROM alerts WHERE priority = 'HIGH') as high_alerts,
    (SELECT COUNT(*) FROM clinical_notes) as notes;

-- Expected: patients=1, doctors=1, consents=2, lab_values=6, vitals=14, high_alerts=1, notes=1
```

---

## Narrative Talking Points (For Demo Video)

**Segment 1: Patient's Experience**
- "Riya uploaded her old blood test and saw it showed low hemoglobin at 9.8."
- "Within 30 days, her watch data revealed a pattern: elevated heart rate and poor sleep."
- "When Delhi's heat wave hit, air quality dropped dramatically to AQI 145."

**Segment 2: System Intelligence**
- "The system correlated all three factors: lab findings, wearable patterns, and environmental stress."
- "In seconds, it calculated the combined risk and generated a HIGH priority alert."
- "Dr. Priya received the alert immediately on her dashboard."

**Segment 3: Doctor's Action**
- "Dr. Priya reviewed Riya's case - all evidence presented in one unified view."
- "She made clinical decisions: start iron supplementation, minimize outdoor exposure."
- "She documented everything for future reference and continuity of care."

**Segment 4: Patient Empowerment**
- "When Riya asked 'Why did I get this alert?', the AI explained in plain language."
- "It connected all the dots: anemia, heart rate strain, air pollution, poor sleep."
- "Riya immediately understood the causation and importance of following Dr. Priya's advice."

---

## Database Schema Notes

All tables referenced must exist with these minimum fields:

```
users: id, email, full_name, role, status
consent_records: id, patient_id, doctor_id, scope, status
medical_reports: id, patient_id, report_type, extraction_status
lab_values: id, report_id, test_name, value, status
wearable_vitals: id, patient_id, metric_type, value, reading_timestamp
environmental_data: id, patient_id, aqi_value, recorded_at
alerts: id, patient_id, priority, status, evidence
clinical_notes: id, alert_id, doctor_id, recommendations
voice_queries: id, patient_id, question, created_at
voice_responses: id, query_id, response_text, confidence_score
scheduled_tasks: id, patient_id, trigger_date, status
```

---

## Success Metrics

After seeding, demo should show:

✅ Patient can log in and see their full health dashboard  
✅ Doctor can log in and see Riya as a HIGH-priority patient  
✅ All evidence is visible and connected (lab + vitals + environment)  
✅ Doctor can review alert and acknowledge with clinical note  
✅ Patient voice query returns comprehensive, grounded explanation  
✅ System is performant (queries return in <2 seconds)  
✅ Data is consistent across all views  

---

## Rollback Instructions

If seeding needs to be undone:

```sql
-- Delete in reverse order (respecting foreign keys)
DELETE FROM voice_responses WHERE patient_id = 'user_riya_001';
DELETE FROM voice_queries WHERE patient_id = 'user_riya_001';
DELETE FROM scheduled_tasks WHERE patient_id = 'user_riya_001';
DELETE FROM clinical_notes WHERE patient_id = 'user_riya_001';
DELETE FROM alert_notifications WHERE alert_id IN (
    SELECT id FROM alerts WHERE patient_id = 'user_riya_001'
);
DELETE FROM alerts WHERE patient_id = 'user_riya_001';
DELETE FROM environmental_data WHERE patient_id = 'user_riya_001';
DELETE FROM vitals_summary WHERE patient_id = 'user_riya_001';
DELETE FROM wearable_vitals WHERE patient_id = 'user_riya_001';
DELETE FROM report_insights WHERE report_id IN (
    SELECT id FROM medical_reports WHERE patient_id = 'user_riya_001'
);
DELETE FROM lab_values WHERE report_id IN (
    SELECT id FROM medical_reports WHERE patient_id = 'user_riya_001'
);
DELETE FROM medical_reports WHERE patient_id = 'user_riya_001';
DELETE FROM consent_records WHERE patient_id = 'user_riya_001';
DELETE FROM users WHERE id IN ('user_riya_001', 'user_doc_priya_001');
```

---

**Generated**: 2026-04-03 by QA Gatekeeper  
**Seed Data Version**: 1.0  
**Ready for Production Demo**: YES ✅