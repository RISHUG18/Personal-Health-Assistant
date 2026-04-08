# Personal Health Assistant — Backend API Reference

## Overview

This backend is a FastAPI application that turns raw medical lab reports into **structured data**, provides a **doctor dashboard**, and exposes APIs for wearable vitals, health summaries, intelligent alerts, and RAG-powered voice/text queries.

The ingestion pipeline is fully automatic: uploading a report via `POST /reports/ingest` triggers Tesseract OCR and Gemini AI extraction without any further client action.

---

## Architecture

### Report Ingestion Pipeline

```
PDF / Image
     │
     ▼
┌──────────────────────────────┐
│  Upload to Supabase Storage  │  ← synchronous, returns report_id
│  + pending DB row            │  POST /reports/ingest  (202 Accepted)
└──────────────┬───────────────┘
               │  background task (async, per-client)
               ▼
┌──────────────────────────────┐  processing_status: pending
│  Tesseract OCR               │  → ocr_complete
│  preprocess_image()          │
│  run_ocr() per page          │  ocr_engine = "tesseract"
│  → medical_reports.ocr_text  │  ocr_confidence stored
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐  processing_status: ocr_complete
│  Gemini AI Extraction        │  → done
│  extract_with_gemini(text)   │
│  → lab_results table         │
└──────────────────────────────┘

Poll: GET /reports/status/{report_id}
```

### Alerts Pipeline

```
lab_results
     │
     ▼
POST /alerts/evaluate/{user_id}
     │  deterministic rules evaluated
     ▼
alerts + alert_evidence
     │
     ▼
GET /alerts/{user_id}
```

---

## Backend Folder Structure

```
backend/
├── main.py                      # FastAPI app entrypoint + router registration
├── requirements.txt             # Python dependencies
│
├── config/
│   └── supabase_client.py       # Supabase client + env helpers
│
├── controllers/
│   ├── reports_controller.py    # Ingest pipeline (upload → OCR → Gemini)
│   ├── doctor_controller.py     # Doctor dashboard business logic
│   └── users_controller.py      # User CRUD business logic
│
├── routes/
│   ├── reports.py               # 4 endpoints — ingest, list, status, lab-results
│   ├── doctor.py                # Doctor dashboard endpoints (/api/v1/doctor/*)
│   ├── alerts.py                # GET/POST /alerts/*
│   ├── auth.py                  # POST /auth/register, POST /auth/login
│   ├── users.py                 # /api/v1/users/* (CRUD)
│   ├── upload.py                # POST /upload/report (JWT-protected direct upload)
│   ├── vitals.py                # POST /api/v1/ingest/vitals, GET /api/v1/vitals/*
│   ├── environment.py           # GET /api/v1/environment/aqi
│   ├── summaries.py             # GET/POST /api/v1/summaries/*
│   ├── rag.py                   # POST /api/v1/rag/query
│   ├── voice.py                 # POST /api/v1/voice/*
│   └── debug.py                 # Internal diagnostics
│
├── ocr/                         # Tesseract OCR module
│   ├── preprocessor.py          # Grayscale → denoise → threshold → deskew
│   ├── ocr_engine.py            # pytesseract wrapper → (text, confidence)
│   └── pipeline.py              # Legacy regex pipeline (not used by main flow)
│
├── extraction/                  # Gemini AI extraction module
│   ├── gemini_extractor.py      # extract_with_gemini(ocr_text) — text-only call
│   ├── models.py                # Pydantic models for Gemini response
│   ├── normalizer.py            # Unit/date normalization
│   ├── inserter.py              # Idempotent DB insertion into lab_results
│   └── pipeline.py              # process_report_with_gemini() orchestrator
│
├── rules/                       # Deterministic health rules engine
│   ├── definitions.py           # Rule functions (anemia, cholesterol, glucose…)
│   ├── engine.py                # evaluate_rules() → List[AlertRecord]
│   ├── inserter.py              # persist_alerts() — idempotent DB write
│   ├── models.py                # AlertRecord, Severity, EvidenceRef
│   ├── environment.py           # Environmental modifiers (AQI, temperature)
│   └── config.json              # Threshold configuration
│
├── middleware/
│   └── auth_middleware.py       # get_current_user, get_current_user_with_role, verify_service_role
│
├── models/
│   └── user.py                  # UserCreate, UserResponse, UserUpdate Pydantic models
│
├── services/                    # Shared services
│   ├── wearable.py              # Wearable vitals ingestion + aggregation
│   ├── context/                 # Context builder for RAG
│   ├── embeddings/              # SentenceTransformers embedding
│   ├── preprocessing/           # Text cleaning & chunking
│   └── retrieval/               # Vector retrieval (pgvector, FAISS)
│
├── prompts/                     # System prompts for LLM roles
├── scripts/                     # Cron jobs and utility scripts
└── tests/                       # Unit test suite
```

---

## Setup

### 1. Environment Variables

Create `src/backend/.env`:

```env
# Supabase (required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_REPORTS_BUCKET=medical-reports
SUPABASE_OCR_REPORTS_TABLE=medical_reports

# Gemini AI (required for lab extraction)
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.1-pro-preview   # default if unset
```

### 2. System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr poppler-utils

# macOS
brew install tesseract poppler
```

### 3. Python Dependencies

```bash
cd src
pip install -r backend/requirements.txt
```

### 4. Database Migrations

Run in order in the Supabase SQL editor:

```sql
-- db/schema.sql                            — base tables
-- db/migrations/001_add_report_chunks.sql  — RAG chunks
-- db/migrations/002_add_report_chunk_metadata.sql
-- db/migrations/003_add_processing_status.sql  — async pipeline columns
```

### 5. Start the Server

```bash
cd src
PYTHONPATH=. uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

---

## API Endpoints

All endpoints requiring authentication use `Authorization: Bearer <JWT_ACCESS_TOKEN>`.

---

### Authentication

#### `POST /auth/register`

Register a new user. Bypasses email confirmation via the Supabase Admin API and returns a valid JWT immediately. Atomically rolls back the Auth record if the DB mapping fails.

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "Secret123!", "full_name": "Arjun Sharma", "role": "patient"}'
```

Response `201`:
```json
{
  "message": "User registered successfully",
  "user_id": "550e8400-...",
  "access_token": "eyJ...",
  "refresh_token": "..."
}
```

`role` must be `"patient"` or `"doctor"`.

---

#### `POST /auth/login`

Authenticate and get JWT tokens. Updates `users.last_login_at`.

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "Secret123!"}'
```

---

### Report Ingestion

#### Report Ingestion — All Endpoints

> **OCR is always Tesseract (local). Gemini only reads the stored OCR text — it never sees the image/PDF directly.**

#### `POST /reports/ingest` ★ — Android + Recommended path

**This is the only upload endpoint the Android app actually calls** (`ReportUploadViewModel.uploadAndProcess()` → `repository.ingestReport()`). Upload a PDF or image; Tesseract OCR and Gemini lab extraction run automatically in the background. Returns **HTTP 202** immediately with a `report_id`. The Android app then polls status every 2 seconds for up to 2 minutes.

```bash
curl -X POST http://localhost:8000/reports/ingest \
  -F "user_id=550e8400-..." \
  -F "user_name=Arjun Sharma" \
  -F "file=@/path/to/report.pdf"
```

Response `202`:
```json
{
  "report_id": "a1b2c3d4-...",
  "storage_path": "Arjun_Sharma_550e8400-.../20260406T120000Z_abc_report.pdf",
  "public_url": "https://...",
  "processing_status": "pending",
  "message": "Report queued. Poll GET /reports/status/{report_id} for progress."
}
```

Pipeline stages:

| `processing_status` | Meaning |
|---------------------|---------|  
| `pending` | Uploaded; Tesseract OCR not yet started |
| `ocr_complete` | Tesseract done, text stored; Gemini extraction running |
| `done` | Lab results written to `lab_results` table |
| `failed` | Error — see `processing_error` field |

---

#### `GET /reports` — Android report history screen

Returns a paginated list of reports for a user. Used by the Android app's report history screen.

```bash
curl "http://localhost:8000/reports?user_id=550e8400-...&limit=20&offset=0"
```

Response:
```json
{
  "items": [{"id": "...", "source_file_name": "report.pdf", "processing_status": "done", ...}],
  "total": 5,
  "limit": 20,
  "offset": 0
}
```

---

#### `GET /reports/status/{report_id}` — Android polling

Poll processing progress after `/reports/ingest`. The Android app polls every 2 seconds.

```bash
curl http://localhost:8000/reports/status/a1b2c3d4-...
```

Response while processing: `{"processing_status": "ocr_complete", "ocr_confidence": 91.4, ...}`  
Response when done: `{"processing_status": "done", "ocr_confidence": 91.4, "lab_results_count": 18}`

---

#### `GET /reports/{report_id}/lab-results` — Android lab results screen

Returns all structured lab results Gemini extracted from a report's OCR text.

```bash
curl http://localhost:8000/reports/a1b2c3d4-.../lab-results
```



### Protected Upload (JWT)

#### `POST /upload/report`

JWT-protected direct upload to the `medical-reports` storage bucket. Records the upload in `structured_reports`. Does **not** trigger OCR or extraction — use `/reports/ingest` for the full pipeline.

```bash
curl -X POST http://localhost:8000/upload/report \
  -H "Authorization: Bearer <JWT>" \
  -F "file=@/path/to/report.pdf"
```

---

### Alerts

#### `POST /alerts/evaluate/{user_id}` — JWT required

Run the deterministic rules engine for the authenticated user. Evaluates all configured health rules against their lab data. **Idempotent** — replaces previous alerts.

```bash
curl -X POST http://localhost:8000/alerts/evaluate/550e8400-... \
  -H "Authorization: Bearer <JWT>" \
  -G --data-urlencode "location=Mumbai" \
  --data-urlencode "date=2026-04-06"
```

Response:
```json
{
  "user_id": "550e8400-...",
  "alerts_triggered": 3,
  "deleted": 2,
  "inserted": 3,
  "evidence_inserted": 5,
  "errors": []
}
```

---

#### `POST /alerts/admin/evaluate/{user_id}` — Service role only

Same as above but secured with `SUPABASE_SERVICE_ROLE_KEY`. Called by the **nightly cron job** to evaluate all patients automatically.

---

#### `GET /alerts/{user_id}` — JWT required

Fetch all stored alerts for the authenticated user, with optional evidence linking back to specific lab results.

```bash
# With evidence (default)
curl http://localhost:8000/alerts/550e8400-... \
  -H "Authorization: Bearer <JWT>"

# Without evidence
curl "http://localhost:8000/alerts/550e8400-...?include_evidence=false" \
  -H "Authorization: Bearer <JWT>"
```

Response:
```json
{
  "user_id": "550e8400-...",
  "count": 2,
  "alerts": [
    {
      "id": "...",
      "severity": "high",
      "reason": "Hemoglobin 11.2 g/dL — below normal (< 12 g/dL)",
      "created_at": "2026-04-06T12:00:00+00:00",
      "evidence": [
        {
          "id": "...",
          "report_id": "...",
          "lab_result_id": "...",
          "ocr_text_snippet": "Hemoglobin  11.2  g/dL"
        }
      ]
    }
  ]
}
```

Severity values: `"low"` | `"medium"` | `"high"`

---

### Doctor Dashboard — `/api/v1/doctor/*`

All endpoints require a valid JWT with `role = "doctor"`. Access is additionally gate-kept to only the doctor's **assigned patients** (via `doctor_patient_mapping`).

#### `GET /api/v1/doctor/patients`

List all patients assigned to the authenticated doctor, sorted by risk level (high → medium → low).

```bash
curl http://localhost:8000/api/v1/doctor/patients \
  -H "Authorization: Bearer <DOCTOR_JWT>"
```

Response:
```json
{
  "doctor_id": "...",
  "count": 3,
  "patients": [
    {
      "user_id": "...",
      "name": "Priya Patel",
      "email": "priya@example.com",
      "age": 34,
      "gender": "female",
      "blood_group": "B+",
      "risk_level": "high",
      "alert_counts": {"high": 2, "medium": 1, "low": 0, "total": 3},
      "report_count": 4,
      "last_report_at": "2026-04-01T...",
      "assigned_at": "2026-03-01T..."
    }
  ]
}
```

---

#### `POST /api/v1/doctor/patients`

Add a patient to the doctor's roster by creating a `doctor_patient_mapping` row. The patient must exist and have `role = "patient"`.

```bash
curl -X POST http://localhost:8000/api/v1/doctor/patients \
  -H "Authorization: Bearer <DOCTOR_JWT>" \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "550e8400-..."}'
```

Response `201`:
```json
{
  "doctor_id": "...",
  "patient_id": "550e8400-...",
  "patient_name": "Priya Patel",
  "message": "Patient 'Priya Patel' added successfully."
}
```

Errors: `404` if patient not found, `409` if already assigned.

---

#### `DELETE /api/v1/doctor/patients/{patient_id}`

Remove a patient from the doctor's roster. Deletes the mapping only — **does not delete patient data**.

```bash
curl -X DELETE http://localhost:8000/api/v1/doctor/patients/550e8400-... \
  -H "Authorization: Bearer <DOCTOR_JWT>"
```

Response `200`:
```json
{
  "doctor_id": "...",
  "patient_id": "550e8400-...",
  "message": "Patient removed from your roster successfully."
}
```

Error: `404` if no mapping exists.

---

#### `GET /api/v1/doctor/patients/{patient_id}/summary`

Comprehensive patient overview: profile, report counts, alert severity breakdown, latest health summary, and 7-day wearable vitals snapshot.

```bash
curl http://localhost:8000/api/v1/doctor/patients/550e8400-.../summary \
  -H "Authorization: Bearer <DOCTOR_JWT>"
```

Response:
```json
{
  "patient": {"id": "...", "full_name": "Priya Patel", "age": 34, ...},
  "reports": {"total": 4, "recent": [...]},
  "alerts": {"total": 3, "high": 2, "medium": 1, "low": 0, "recent": [...]},
  "latest_health_summary": {"summary_content": "...", "created_at": "..."},
  "wearable_vitals": {
    "heart_rate": {"avg": 72.5, "min": 58, "max": 110, "latest": 68, "unit": "bpm"},
    "steps": {"avg": 7800, ...}
  }
}
```

---

#### `GET /api/v1/doctor/patients/{patient_id}/reports`

List all medical reports for a patient with lab result counts and processing status.

```bash
curl http://localhost:8000/api/v1/doctor/patients/550e8400-.../reports \
  -H "Authorization: Bearer <DOCTOR_JWT>"
```

---

#### `GET /api/v1/doctor/patients/{patient_id}/reports/{report_id}`

Full detail of a single report: metadata, OCR text, and all extracted lab results.

---

#### `GET /api/v1/doctor/patients/{patient_id}/alerts`

All alerts for a patient with full evidence linking back to lab results and OCR snippets.

---

#### `POST /api/v1/doctor/patients/{patient_id}/evaluate-alerts`

Manually trigger the rules engine for a patient — same logic as the nightly cron, but on demand. Accepts optional `location` and `date` for environmental modifiers.

```bash
curl -X POST http://localhost:8000/api/v1/doctor/patients/550e8400-.../evaluate-alerts \
  -H "Authorization: Bearer <DOCTOR_JWT>" \
  -H "Content-Type: application/json" \
  -d '{"location": "Mumbai", "date": "2026-04-06"}'
```

---

#### `GET /api/v1/doctor/patients/{patient_id}/lab-results`

All lab results across all reports for a patient, grouped by report.

---

### Users — `/api/v1/users/*`

#### `POST /api/v1/users`
Create a user record directly (no auth bypass — use `/auth/register` for sign-up with JWT).

#### `GET /api/v1/users/{user_id}` — JWT required (own profile only)
Fetch a user profile by UUID.

#### `GET /api/v1/users/email/{email}` — JWT required
Fetch a user profile by email address.

#### `PATCH /api/v1/users/{user_id}` — JWT required (own profile only)
Update profile fields (name, phone, city, gender, date_of_birth, blood_group, etc.).

#### `DELETE /api/v1/users/{user_id}` — JWT required (own profile only)
Delete a user and all associated data (cascades on DB).

---

### Wearable Vitals — `/api/v1/vitals/*`

#### `POST /api/v1/ingest/vitals` — JWT required

Batch ingest vital readings from wearable devices (Fitbit, Apple Watch, etc.). Duplicates are silently skipped.

```bash
curl -X POST http://localhost:8000/api/v1/ingest/vitals \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-...",
    "readings": [
      {"recorded_at": "2026-04-06T10:30:00Z", "metric_type": "heart_rate", "value": 72, "unit": "bpm"},
      {"recorded_at": "2026-04-06T10:30:00Z", "metric_type": "steps", "value": 5432, "unit": "steps"}
    ]
  }'
```

Supported `metric_type` values: `heart_rate`, `steps`, `sleep_minutes`, `deep_sleep_minutes`, `calories_burned`, `active_minutes`, `spo2`, `hrv_ms`, `resting_heart_rate`, `sleep_score`.

---

#### `GET /api/v1/vitals/{user_id}/summary?days=7` — JWT required

Aggregated vitals: avg, min, max, latest per metric over the specified window (1–30 days). Used by the context builder for AI queries.

---

#### `GET /api/v1/vitals/{user_id}/readings` — JWT required

Raw individual readings (not aggregated). Supports filtering by `metric_type`, `days`, and `limit`.

---

### Health Summaries — `/api/v1/summaries/*` — JWT required

#### `POST /api/v1/summaries/generate/{user_id}`
Generate a weekly AI health summary (via Gemini) for the user. Summaries are stored with `target_role = "patient"` or `"doctor"`.

#### `GET /api/v1/summaries/{user_id}`
Retrieve all stored health summaries for the user.

---

### Environment

#### `GET /api/v1/environment/aqi?location=Mumbai`

Fetch real-time AQI and weather data via Open-Meteo. Used by the rules engine for environmental severity modifiers.

---

### RAG Query

#### `POST /api/v1/rag/query` — JWT required

Natural-language query against the user's medical history. Retrieves relevant report chunks via vector search and sends to an LLM for answer synthesis.

```bash
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "550e8400-...", "query": "What was my hemoglobin level last month?"}'
```

---

### Voice

#### `POST /api/v1/voice/query` — JWT required
Submit a voice/text health query. Returns a structured AI response with citations.

---

## Rules Engine

The rules engine is a **deterministic, zero-LLM alert system** that evaluates lab data against configured health thresholds.

### Architecture

```
backend/rules/
├── config.json      # All thresholds (editable without code changes)
├── definitions.py   # Rule functions — pure, no DB access
├── engine.py        # evaluate_rules(client, user_id) → List[AlertRecord]
├── inserter.py      # persist_alerts() — idempotent DB persistence
├── models.py        # AlertRecord, Severity
└── environment.py   # Environmental risk modifiers
```

### Configured Rules

| Rule | What it checks | Severity |
|------|---------------|---------|
| `any_abnormal` | Any flagged abnormal lab value | HIGH (≥3 flagged), MEDIUM (1–2) |
| `low_hemoglobin` | Hemoglobin < 12 g/dL | HIGH (< 8), MEDIUM (8–12) |
| `high_cholesterol` | Total cholesterol ≥ 200 mg/dL | HIGH (> 240), LOW (200–240) |
| `high_ldl` | LDL ≥ 160 mg/dL | HIGH (> 190), MEDIUM (160–190) |
| `high_blood_sugar` | Fasting glucose ≥ 100 mg/dL | HIGH (> 126), MEDIUM (100–126) |
| `high_hba1c` | HbA1c ≥ 5.7% | HIGH (≥ 6.5), MEDIUM (5.7–6.5) |
| `abnormal_tsh` | TSH < 0.4 or > 4.5 µIU/mL | HIGH (> 10), MEDIUM (other) |
| `low_vitamin_d` | Vitamin D < 30 ng/mL | HIGH (< 12), MEDIUM (12–30) |
| `low_b12` | Vitamin B12 < 300 pg/mL | HIGH (< 150), MEDIUM (150–300) |
| `high_creatinine` | Creatinine ≥ 1.3 mg/dL | HIGH (> 2.0), MEDIUM (1.3–2.0) |
| `low_platelets` | Platelet count < 150 ×10³/µL | HIGH (< 50), MEDIUM (50–150) |
| `abnormal_wbc` | WBC < 2 or > 11 ×10³/µL | HIGH (< 2 or > 15), MEDIUM (other) |
| `missing_critical_tests` | Missing CBC or metabolic panel | LOW |

### Environmental Modifiers

When environmental data is available, the engine escalates alert severity:

| Condition | Affected Rules | Effect |
|-----------|---------------|--------|
| Poor air quality (AQI > 100) | `abnormal_wbc`, `low_hemoglobin` | Severity +1 tier |
| High temperature (> 30°C) | `abnormal_tsh`, `low_vitamin_d` | Severity +1 tier |
| Extreme conditions (AQI > 150 or temp > 35°C) | `any_abnormal`, `low_b12` | Advisory appended |

---

## Database Schema

### `medical_reports`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | Report owner |
| `report_date` | DATE | Date extracted by Gemini |
| `report_type` | TEXT | Report type extracted by Gemini |
| `source_file_name` | TEXT | Original filename |
| `source_url` | TEXT | Supabase Storage URL |
| `ocr_text` | TEXT | Full Tesseract OCR output (nullable during processing) |
| `ocr_engine` | TEXT | Always `"tesseract"` |
| `ocr_confidence` | NUMERIC | Average Tesseract confidence (0–100) |
| `processing_status` | TEXT | `pending \| ocr_complete \| done \| failed` |
| `processing_error` | TEXT | Error detail when status is `failed` |

### `lab_results`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `report_id` | UUID | FK → `medical_reports.id` |
| `test_name` | TEXT | Lab test name (OCR-corrected by Gemini) |
| `value` | NUMERIC | Numeric result (NULL for qualitative) |
| `unit` | TEXT | Measurement unit as printed |
| `reference_range` | TEXT | Normal range as printed |
| `abnormal_flag` | BOOLEAN | True if marked outside normal range |
| `extracted_from_page` | INT | Page number |

### `alerts`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | Alert owner |
| `severity` | TEXT | `low \| medium \| high` |
| `reason` | TEXT | Human-readable explanation |
| `created_at` | TIMESTAMP | Generation time |

### `alert_evidence`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `alert_id` | UUID | FK → `alerts.id` (CASCADE DELETE) |
| `report_id` | UUID | FK → `medical_reports.id` |
| `lab_result_id` | UUID | FK → `lab_results.id` |
| `ocr_text_snippet` | TEXT | Raw OCR excerpt that triggered the alert |

### `doctor_patient_mapping`

| Column | Type | Description |
|--------|------|-------------|
| `doctor_id` | UUID | FK → `users.id` |
| `patient_id` | UUID | FK → `users.id` |
| `created_at` | TIMESTAMP | When the mapping was created |

### `wearable_vitals`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | Data owner |
| `recorded_at` | TIMESTAMP | Measurement timestamp |
| `metric_type` | TEXT | e.g. `heart_rate`, `steps` |
| `value` | NUMERIC | Reading value |
| `unit` | TEXT | e.g. `bpm`, `steps` |
| `device_id` | TEXT | Optional device identifier |

---

## Key Design Decisions

1. **Single ingest entry point**: `POST /reports/ingest` is the only way to upload and process a report. Low-level step endpoints (`/upload`, `/ocr`, `/extract-labs-gemini`, `/process`) have been removed — they were redundant and created multiple code paths to maintain.

2. **Two-stage pipeline, two tools**: Tesseract handles OCR (local, fast, deterministic, no API cost). Gemini handles structured extraction from the OCR text (smart, handles OCR noise and format variation). The OCR text is stored immutably; Gemini reads it.

3. **Async-first**: `POST /reports/ingest` returns HTTP 202 immediately. OCR and Gemini run as a FastAPI `BackgroundTask` — multiple clients are processed in parallel, none blocking the server.

4. **Doctor dashboard authorization is two-layered**: JWT verifies `role = "doctor"`, then every patient-specific endpoint additionally verifies a `doctor_patient_mapping` row exists. Accessing a patient you're not mapped to returns 403.

5. **Idempotent operations**: Re-submitting a report to ingest, re-running alert evaluation, re-generating a health summary — all produce a clean slate by deleting previous rows before inserting fresh ones.

6. **Pure rules functions**: Alert rules in `backend/rules/definitions.py` receive only a `user_id` and a list of `LabRow` objects — no database calls inside rule logic. This makes every rule independently unit-testable without credentials or mocking.

7. **Status polling over webhooks**: Pipeline status is a column in `medical_reports`, so the client polls `GET /reports/status/{report_id}` without requiring WebSockets or push infrastructure.
