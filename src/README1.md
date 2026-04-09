# Personal Health Assistant — Backend API and Privacy Reference

## Overview

This backend is a FastAPI application for:
- user registration and login via Supabase Auth
- patient profile management
- medical report upload, OCR, and Gemini-based extraction
- doctor-patient roster management
- alerts, summaries, vitals, and environment context
- privacy workflows needed for GDPR-style and DPDP-style compliance

The current privacy model includes:
- authenticated access control on user-scoped resources
- doctor-safe patient lookup for roster assignment
- account export in machine-readable JSON
- account deletion that removes database data, storage objects, and auth identity
- persisted `storage_path` metadata so uploaded files can be physically deleted

## Important Privacy Notes

- Health data is treated as highly sensitive.
- Report deletion is not complete unless both:
  - database rows are removed
  - Supabase Storage objects are removed
- Gemini usage must be contractually approved for health data handling.
- Set `GEMINI_DATA_PROCESSING_APPROVED=true` only after your team has verified that your Gemini plan/contract does not use customer health data for model training.

## Architecture

### Report Ingestion Flow

```text
Client upload
  -> Supabase Storage
  -> medical_reports row created with processing_status='pending'
  -> background OCR with Tesseract
  -> Gemini extracts structured labs from OCR text
  -> lab_results persisted
  -> report status becomes done or failed
```

### Privacy Flow

```text
DELETE /api/v1/users/me
  -> enumerate user storage paths
  -> delete files from Supabase Storage
  -> delete public.users row
  -> delete Supabase Auth user
```

### Doctor Add-Patient Flow

```text
Doctor dashboard
  -> GET /api/v1/doctor/patients/lookup?email=...
  -> POST /api/v1/doctor/patients { patient_id }
```

This lookup endpoint exists because the old `GET /api/v1/users/email/{email}` route was removed in favor of a dedicated doctor-safe lookup flow.

## Key Backend Files

```text
backend/
├── main.py
├── routes/
│   ├── auth.py
│   ├── users.py
│   ├── reports.py
│   ├── upload.py
│   ├── alerts.py
│   ├── summaries.py
│   ├── vitals.py
│   ├── environment.py
│   └── doctor.py
├── controllers/
│   ├── users_controller.py
│   ├── reports_controller.py
│   └── doctor_controller.py
├── services/
│   ├── privacy.py
│   ├── llm/
│   ├── wearable/
│   ├── environment/
│   └── summaries/
└── extraction/
    ├── gemini_extractor.py
    ├── inserter.py
    └── pipeline.py
```

## Environment Variables

Create `src/backend/.env` or provide equivalent runtime env vars:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_REPORTS_BUCKET=medical-reports
SUPABASE_OCR_REPORTS_TABLE=medical_reports

GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.1-pro-preview

# Set only after legal / vendor review is complete
GEMINI_DATA_PROCESSING_APPROVED=true
```

## Setup

### Python dependencies

```bash
cd src
pip install -r backend/requirements.txt
```

### System dependencies

```bash
# Ubuntu / Debian
sudo apt-get install tesseract-ocr poppler-utils

# macOS
brew install tesseract poppler
```

### Run the server

```bash
cd src
PYTHONPATH=. uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Docs:
- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

## Database Migrations

Apply your base schema first, then migrations.

Recommended order:

```text
db/schema.sql
db/migrations/001_add_report_chunks.sql
db/migrations/002_add_report_chunk_metadata.sql
db/migrations/004_add_processing_status.sql
db/migrations/006_add_environmental_data.sql
db/migrations/007_add_env_evidence_to_alert_evidence.sql
db/migrations/008_add_wearable_vitals.sql
db/migrations/009_auth_and_reports.sql
db/migrations/010_vitals_cleanup_job.sql
db/migrations/011_add_health_summaries.sql
db/migrations/012_add_text_value_to_lab_results.sql
db/migrations/015_privacy_hardening.sql
```

### New privacy migration

`db/migrations/015_privacy_hardening.sql` adds or enforces:
- `storage_path` on `medical_reports`
- `storage_path` on `structured_reports`
- RLS enablement for backend-used tables
- doctor and patient access policies on reports, labs, alerts, evidence, vitals, summaries
- self-delete policy on `users`
- idempotent weekly cleanup scheduling for stale health summaries

The migration is guarded with existence checks so it does not fail on deployments where some tables are managed outside this repo.

## Authentication APIs

All protected endpoints require:

```text
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

### `POST /auth/register`

Registers a user in Supabase Auth and mirrors them into `public.users`.

Example:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor1@example.com",
    "password": "StrongPassword123!",
    "full_name": "Dr. Ananya Mehta",
    "role": "doctor"
  }'
```

### `POST /auth/login`

Authenticates a user and returns access and refresh tokens.

## User APIs

Base prefix: `/api/v1/users`

### API changes summary: old -> new

- Old: `POST /api/v1/users`
  New: `POST /auth/register`

- Old: `GET /api/v1/users/{user_id}` for self-profile fetch
  New: `GET /api/v1/users/me`

- Old: `PATCH /api/v1/users/{user_id}` for self-profile update
  New: `PATCH /api/v1/users/me`

- Old: destructive deletion expected a path user id such as `DELETE /api/v1/users/{user_id}`
  New: `DELETE /api/v1/users/me`

- Old: `GET /api/v1/users/email/{email}` could be used by clients for cross-user lookup
  New: `GET /api/v1/doctor/patients/lookup?email=<email>` for doctor patient search

- Old: no self-service export endpoint
  New: `GET /api/v1/users/me/export`

### Removed redundant endpoints

- Removed: `POST /api/v1/users`
  Reason: it created a `public.users` row without the corresponding Supabase Auth identity. `/auth/register` is the correct canonical signup flow.

- Removed: `DELETE /api/v1/users/{user_id}`
  Reason: it duplicated `DELETE /api/v1/users/me` while pretending to accept an arbitrary user id. Self-delete should always be JWT-derived.

- Removed: `GET /api/v1/users/email/{email}`
  Reason: it overlapped with doctor lookup and encouraged cross-user lookup behavior. Doctor lookup now has its own dedicated route.

### `GET /api/v1/users/me`

Returns the authenticated user's own profile.

### `PATCH /api/v1/users/me`

Updates the authenticated user's own profile.

### Hidden compatibility routes

These are still implemented for older clients but intentionally hidden from the OpenAPI schema:
- `GET /api/v1/users/{user_id}` for self-profile fetch only
- `PATCH /api/v1/users/{user_id}` for self-profile update only

Both compatibility routes reject cross-user access and should be migrated to `/me`.

### `GET /api/v1/users/me/export`

Exports all currently stored user data as a JSON attachment.

Included datasets may contain:
- `profile`
- `medical_reports`
- `lab_results`
- `structured_reports`
- `health_summaries`
- `wearable_vitals`
- `environmental_data`
- `alerts`
- `alert_evidence`
- `doctor_patient_mapping`

### `DELETE /api/v1/users/me`

Deletes the authenticated user's account and associated storage-backed report files.

Current deletion sequence:
1. fetch report storage paths
2. remove files from Supabase Storage
3. delete `public.users`
4. delete Supabase Auth identity

## Doctor APIs

Base prefix: `/api/v1/doctor`

All doctor endpoints require the authenticated user to have `role='doctor'`.

### API changes summary: old -> new

- Old: doctor dashboard patient lookup used `GET /api/v1/users/email/{email}`
  New: `GET /api/v1/doctor/patients/lookup?email=<email>`

- Old: patient lookup could collide with self-only profile restrictions
  New: doctor lookup is separated into a doctor-authorized endpoint that only resolves `role='patient'`

### `GET /api/v1/doctor/patients`

List assigned patients.

### `GET /api/v1/doctor/patients/lookup?email=<email>`

Resolve a patient by email before creating a doctor-patient mapping.

This endpoint:
- verifies the caller is a doctor
- only resolves rows whose `role='patient'`
- returns `patient_id`, `email`, and `full_name`

### `POST /api/v1/doctor/patients`

Create a doctor-patient mapping.

Request:

```json
{
  "patient_id": "uuid"
}
```

### `DELETE /api/v1/doctor/patients/{patient_id}`

Remove a doctor-patient mapping.

### `GET /api/v1/doctor/patients/{patient_id}/summary`

Patient summary for doctor view.

### `GET /api/v1/doctor/patients/{patient_id}/reports`

List patient reports.

### `GET /api/v1/doctor/patients/{patient_id}/reports/{report_id}`

Detailed report view.

### `GET /api/v1/doctor/patients/{patient_id}/alerts`

Fetch patient alerts with evidence. Environmental evidence is now returned from the dedicated `environmental_evidence` column instead of being embedded into OCR snippet text.

### `GET /api/v1/doctor/patients/{patient_id}/lab-results`

Fetch patient lab results grouped by report.

### `POST /api/v1/doctor/patients/{patient_id}/evaluate-alerts`

Manually recompute alerts.

### `POST /api/v1/doctor/patients/{patient_id}/generate-summary`

Generate fresh summaries for the assigned patient.

## Report APIs

Base prefix: `/reports`

### API changes summary: old -> new behavior

- Old: upload flows did not reliably persist `storage_path`
  New: `POST /reports/ingest` persists `storage_path` so account deletion can remove physical files

- Old: report access relied more heavily on application flow assumptions
  New: `GET /reports`, `GET /reports/status/{report_id}`, `GET /reports/{report_id}/lab-results`, and `GET /reports/{report_id}/download_url` are enforced as authenticated owner-only operations

- Old: report downloads could be treated as ordinary stored URLs
  New: `GET /reports/{report_id}/download_url` returns a short-lived signed URL for the authenticated owner

### `POST /reports/ingest`

Protected upload endpoint for the main OCR + extraction flow.

Important:
- the `user_id` form field must match the authenticated JWT user
- `storage_path` is now persisted for later deletion and private download

Response includes:
- `report_id`
- `storage_path`
- `public_url`
- `processing_status`

### `GET /reports`

Returns reports for the authenticated user only.

### `GET /reports/status/{report_id}`

Returns status for a report owned by the authenticated user only.

### `GET /reports/{report_id}/lab-results`

Returns extracted labs for a report owned by the authenticated user only.

### `GET /reports/{report_id}/download_url`

Returns a short-lived signed URL for a privately owned report.

## Structured Upload API

### API changes summary: old -> new behavior

- Old: `POST /upload/report` stored file URL metadata without a guaranteed deletion key
  New: `POST /upload/report` also persists `storage_path` so privacy deletion can remove the actual object from Supabase Storage

### `POST /upload/report`

Protected direct upload endpoint for `structured_reports`.

Now stores:
- `storage_path`
- `file_url`
- `report_id`

This change is required so account deletion can remove physical files from Storage.

## Alerts APIs

Base prefix: `/alerts`

### API changes summary: old -> new behavior

- Old: environmental alert evidence could be mixed into OCR text fields
  New: alert evidence now uses the dedicated `environmental_evidence` column

- Old: alert reads and evaluations were less explicit about authenticated ownership
  New: alert endpoints are aligned with authenticated user access rules

### `GET /alerts/{user_id}`

Returns alerts for the authenticated user.

Evidence rows may now include:
- `ocr_text_snippet`
- `environmental_evidence`

### `POST /alerts/evaluate/{user_id}`

Evaluate alerts for the authenticated user.

### `POST /alerts/admin/evaluate/{user_id}`

Service-role protected evaluation endpoint for cron or internal automation.

## Summaries APIs

Base prefix: `/api/v1/summaries`

### `GET /api/v1/summaries/{target_user_id}`

Role-aware summary fetch:
- patients can fetch only their own `target_role='user'` summaries
- doctors can fetch doctor-facing summaries for assigned patients

### `POST /api/v1/summaries/generate/{target_user_id}`

Service-role protected summary generation endpoint.

Retention:
- `health_summaries` rows older than 1 year are scheduled for purge

## Frontend Client Changes

Updated app code:

### `src/frontend/js/doctor-api.js`

Changed patient add flow to:
1. `GET /api/v1/doctor/patients/lookup?email=...`
2. `POST /api/v1/doctor/patients`

Added privacy helpers for doctor dashboard:
- `GET /api/v1/users/me/export`
- `DELETE /api/v1/users/me`

### `src/frontend/doctor-dashboard.html`

Doctor dashboard sidebar now includes:
- `Export My Data`
- `Delete My Account`

These call the privacy-safe endpoints through `DoctorAPI`.

### `src/frontend/js/api.js`

Added or corrected client helpers for:
- authenticated headers using `hc_access_token`
- `GET /alerts/{user_id}`
- `GET /reports`
- `GET /reports/status/{report_id}`
- `GET /reports/{report_id}/lab-results`
- `GET /reports/{report_id}/download_url`
- `GET /users/me`
- `PATCH /users/me`
- `GET /users/me/export`
- `DELETE /users/me`

## Mobile Client Contract Notes

No Android source files were changed as part of this backend/privacy update.

Any mobile client should align with the backend contract below:

### Old API -> new API

- Old: `POST /api/v1/users`
  New: `POST /auth/register`

- Old: `GET /api/v1/users/{user_id}`
  New: `GET /api/v1/users/me`

- Old: `PATCH /api/v1/users/{user_id}`
  New: `PATCH /api/v1/users/me`

- Old: `DELETE /api/v1/users/{user_id}`
  New: `DELETE /api/v1/users/me`

- Old: no export endpoint
  New: `GET /api/v1/users/me/export`

- Old: `GET /api/v1/users/email/{email}` for doctor-side patient lookup
  New: `GET /api/v1/doctor/patients/lookup?email=...`

### Keep using

- `POST /auth/login`
- `POST /auth/register`
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`
- `GET /alerts/{user_id}`
- `GET /reports`
- `GET /reports/status/{report_id}`
- `GET /reports/{report_id}/lab-results`
- `GET /reports/{report_id}/download_url`
- `POST /reports/ingest`

### Use these privacy-safe endpoints

- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`
- `GET /api/v1/users/me/export`
- `DELETE /api/v1/users/me`

Why:
- account deletion now removes Supabase Storage objects and the Supabase Auth identity
- destructive self-delete must be derived from the caller JWT, not from a user id in the path
- export is now available as a dedicated self-service endpoint

### Doctor lookup change

Do not use:
- `GET /api/v1/users/email/{email}`

Use instead:
- `GET /api/v1/doctor/patients/lookup?email=...`

### Signup change

Do not use:
- `POST /api/v1/users`

Use instead:
- `POST /auth/register`

### Live E2E contract test

Run this script against a running backend to verify the current contract end to end:

```bash
cd src
python backend/scripts/test_privacy_contract_e2e.py
```

Optional environment variables:
- `E2E_BASE_URL`
- `E2E_TIMEOUT_SECONDS`

The script verifies:
- `POST /auth/register`
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`
- `GET /api/v1/users/me/export`
- `DELETE /api/v1/users/me`
- hidden compatibility `GET/PATCH /api/v1/users/{user_id}`
- `GET /api/v1/doctor/patients/lookup`
- `POST /api/v1/doctor/patients`
- `GET /api/v1/doctor/patients`
- `DELETE /api/v1/doctor/patients/{patient_id}`
- removed routes stay removed

## Compliance-Oriented Changes Implemented

### Right to be forgotten

Implemented via:
- `DELETE /api/v1/users/me`
- persisted `storage_path`
- Storage object deletion before DB/Auth deletion

### Data portability

Implemented via:
- `GET /api/v1/users/me/export`

### Data minimization and retention

Implemented or documented via:
- wearable vitals retention job
- health summaries retention job
- backend-managed report deletion path

### Access isolation

Implemented via:
- route-level ownership checks
- doctor-specific lookup flow
- RLS migration hardening

### Third-party processor governance

Implemented operationally via:
- `GEMINI_DATA_PROCESSING_APPROVED` warning gate

## Verification Performed

During implementation/review:
- backend compilation passed
- doctor patient lookup route was verified as mounted
- environment rules tests passed
- live E2E contract script added: `backend/scripts/test_privacy_contract_e2e.py`

## Recommended Next Steps

1. Add an inactive-user retention job for uploaded PDFs and report rows.
2. Add API tests for:
   - `GET /api/v1/users/me/export`
   - `DELETE /api/v1/users/me`
   - `GET /api/v1/doctor/patients/lookup`
3. Review Supabase Storage bucket policies to ensure they match the private-download model.

## Final API List

This section is a consolidated index of all currently implemented API endpoints in the backend.

### Health and utility

- `GET /health`
- `GET /api/v1/rag/test`

### Authentication

- `POST /register`
- `POST /login`

### Users

- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`
- `GET /api/v1/users/me/export`
- `DELETE /api/v1/users/me`

Compatibility routes still present for older clients:
- `GET /api/v1/users/{user_id}` (hidden from schema, self-only)
- `PATCH /api/v1/users/{user_id}` (hidden from schema, self-only)

### Doctor

- `GET /api/v1/doctor/patients`
- `GET /api/v1/doctor/patients/lookup?email=...`
- `POST /api/v1/doctor/patients`
- `DELETE /api/v1/doctor/patients/{patient_id}`
- `GET /api/v1/doctor/patients/{patient_id}/summary`
- `GET /api/v1/doctor/patients/{patient_id}/reports`
- `GET /api/v1/doctor/patients/{patient_id}/reports/{report_id}`
- `GET /api/v1/doctor/patients/{patient_id}/alerts`
- `POST /api/v1/doctor/patients/{patient_id}/evaluate-alerts`
- `POST /api/v1/doctor/patients/{patient_id}/generate-summary`
- `GET /api/v1/doctor/patients/{patient_id}/trends`
- `GET /api/v1/doctor/patients/{patient_id}/lab-results`

### Reports

- `POST /reports/ingest`
- `GET /reports`
- `GET /reports/status/{report_id}`
- `GET /reports/{report_id}/lab-results`
- `GET /reports/{report_id}/download_url`

### Structured Upload

- `POST /upload/report`

### Alerts

- `GET /alerts/{user_id}`
- `POST /alerts/evaluate/{user_id}`
- `POST /alerts/admin/evaluate/{user_id}`

### Summaries

- `POST /api/v1/summaries/generate/{target_user_id}`
- `GET /api/v1/summaries/{target_user_id}`

### Vitals

- `POST /api/v1/vitals/ingest`
- `GET /api/v1/vitals/summary/{user_id}`
- `GET /api/v1/vitals/readings/{user_id}`

### Environment

- `GET /api/v1/environment`

### RAG and voice

- `POST /api/v1/rag_query`
- `POST /voice_chat`

### Debug

- `GET /debug/user_data/{email}`
