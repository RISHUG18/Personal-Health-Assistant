# Demo Storyline Seed Pack

This pack defines a single compelling synthetic patient journey that exercises:

- report upload
- wearable sync
- nightly alert cron
- weekly summary generation
- doctor dashboard review
- patient voice assistant question

It is intentionally designed for **staging / demo / QA environments only**.
Do not use it to seed production with live-looking identities.

## Storyline

Patient `Nisha Rao` uploads an older lipid panel showing persistently high LDL.
Over the next two days she syncs wearable data showing elevated resting heart
rate, low sleep, and reduced activity. The nightly alerts cron evaluates her
labs and wearable context and produces a medium-priority cardiovascular risk
alert. A weekly summary is then generated for both patient and doctor views.
Her assigned clinician `Dr. Arjun Mehta` logs in and sees the alert and
summary. Nisha then opens the voice assistant and asks:

`Why did I get an alert?`

## Files

- `storyline.json`
  Synthetic data definition with personas, timing, report context, vitals,
  expected alert, expected doctor summary, and expected patient question.
- `seed-runbook.md`
  Manual runbook describing the recommended order for staging/demo seeding.

## Recommended Flow

1. Create patient and doctor users in a non-production environment.
2. Insert doctor-patient mapping.
3. Upload the historical lipid report for the patient.
4. Run OCR and extraction, then verify `lab_results`.
5. Ingest the wearable vitals time series.
6. Trigger nightly alert evaluation.
7. Trigger summary generation.
8. Verify doctor view.
9. Verify patient voice query.

## Why This Storyline Works

- It feels realistic rather than over-scripted.
- It links historical lab risk with recent wearable drift.
- It produces a meaningful but not overdramatic medium alert.
- It gives both patient and doctor distinct reasons to open the app.
- It ends with a natural voice question that demonstrates grounding.
