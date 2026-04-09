# Seed Runbook: Historical Lipids + Wearables Alert Journey

This runbook is for **staging/demo only**.

## Goal

Create a believable end-to-end story:

1. Patient uploads an old blood test
2. Patient starts syncing wearable data
3. Nightly cron notices older cholesterol risk plus newer wearable drift
4. Medium alert is generated
5. Doctor logs in and sees the patient summary
6. Patient asks the voice assistant: `Why did I get an alert?`

## Recommended Data Story

- Patient: `Nisha Rao`
- Doctor: `Dr. Arjun Mehta`
- Old report: January 2026 lipid panel
- Recent wearable period: April 7-8, 2026
- Alert created: April 9, 2026

## Manual Steps

### 1. Create synthetic users

Create:

- one patient user with role `patient`
- one doctor user with role `doctor`

Use clearly synthetic emails like:

- `demo.nisha.rao@example.test`
- `demo.dr.mehta@example.test`

### 2. Create doctor-patient mapping

Insert one row into `doctor_patient_mapping`:

- `doctor_id = Dr. Arjun Mehta`
- `patient_id = Nisha Rao`

### 3. Seed the historical report

Use the existing report pipeline rather than inserting fake downstream rows first.

Recommended:

1. Upload `Lipid_Panel_Jan2026.pdf`
2. Run OCR
3. Run Gemini extraction

Target lab story:

- Total Cholesterol: `244 mg/dL`
- LDL: `168 mg/dL`
- HDL: `43 mg/dL`
- Triglycerides: `196 mg/dL`

### 4. Seed wearable data

Insert or ingest vitals for two recent days.

Recommended metrics:

- Day 1:
  - resting heart rate `86 bpm`
  - avg heart rate `88 bpm`
  - steps `3920`
  - sleep `341 min`
- Day 2:
  - resting heart rate `91 bpm`
  - avg heart rate `90 bpm`
  - steps `2810`
  - sleep `318 min`
  - active minutes `17`

The intent is to show a mild-to-moderate worsening trend, not a critical emergency.

### 5. Trigger alert generation

Run the alerts evaluation path.

Expected result:

- one medium-severity alert
- evidence linked back to the lipid report and current trend context

Suggested alert narrative:

`Historical cholesterol abnormality combined with recent elevated resting heart rate and reduced activity warrants review.`

### 6. Trigger summary generation

Run weekly summary generation for the same patient.

Expected patient summary:

- easy-to-understand explanation
- grounded in both report and wearable data

Expected doctor summary:

- concise, clinical wording
- references LDL history and recent wearable drift

### 7. Verify doctor journey

Log in as the mapped doctor and verify:

- patient appears in doctor patient list
- patient summary page loads
- medium alert is visible
- summary mentions old lipid abnormality and recent wearable drift

### 8. Verify patient voice journey

Log in as the patient and ask:

`Why did I get an alert?`

Expected answer:

- mentions older cholesterol abnormality
- mentions recent higher resting pulse and lower activity/sleep
- explains why the system generated a medium alert
- stays grounded instead of inventing new diagnoses

## Important Guardrails

- Use `.test` emails or another obviously synthetic domain.
- Do not seed real names, real phone numbers, or real-looking addresses into production.
- Prefer exercising the real upload/OCR/extraction/alert pipeline in staging so the demo remains faithful to product behavior.
