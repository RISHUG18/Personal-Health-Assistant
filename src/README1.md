# Week 2 — Structured Extraction & Database Ingestion

## Overview

This module turns raw PDF/image medical lab reports into **structured rows** in the database.  
The pipeline is fully automatic: uploading a report triggers OCR and Gemini AI extraction without any further client action.

Two ingestion modes are provided:

| Mode | Endpoint | Behaviour |
|------|----------|-----------|
| **Async (recommended)** | `POST /reports/ingest` | Returns HTTP 202 immediately with a `report_id`; OCR + Gemini run in the background |
| **Synchronous** | `POST /reports/process` | Waits for the full pipeline before responding; convenient for scripts |

---

## Architecture

```
PDF / Image
     │
     ▼
┌──────────────────────────┐
│  Upload to Supabase       │  ← runs synchronously, returns report_id
│  Storage + pending row    │  POST /reports/ingest  (202 Accepted)
└──────────┬───────────────┘
           │  background task (async, per-client)
           ▼
┌──────────────────────────┐
│  Tesseract OCR            │
│  preprocessor →           │  processing_status: pending → ocr_complete
│  ocr_engine               │
│  → medical_reports        │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  Gemini AI Extraction     │  processing_status: ocr_complete → done
│  → lab_results            │  POST /reports/extract-labs-gemini
└──────────────────────────┘

Poll progress: GET /reports/status/{report_id}
```

### Alerts pipeline (separate, on-demand)

```
lab_results (from above)
     │
     ▼
POST /alerts/evaluate/{user_id}
     │  13 deterministic rules evaluated
     ▼
alerts + alert_evidence (Supabase)
     │
     ▼
GET /alerts/{user_id}
```

---

## Backend Folder Structure

```
backend/
├── main.py                      # FastAPI app entrypoint
├── requirements.txt             # Python dependencies
├── verify_reports.py            # End-to-end verification script
│
├── config/
│   └── supabase_client.py       # Supabase client + env helpers
│
├── controllers/
│   └── reports_controller.py    # Business logic (upload, OCR, pipeline)
│
├── routes/
│   ├── reports.py               # HTTP routes for report ingestion
│   ├── alerts.py                # HTTP routes for alerts (fetch + evaluate)
│   └── rag.py                   # RAG query pipeline routes
│
├── ocr/                         # OCR module
│   ├── preprocessor.py          # Grayscale → Non-Local Means denoise → deskew
│   ├── ocr_engine.py            # Tesseract OCR wrapper → (text, confidence)
│   ├── pipeline.py              # Legacy regex extraction (not used by main pipeline)
│   └── README.md
│
├── extraction/                  # Gemini AI extraction module
│   ├── gemini_extractor.py      # Gemini API call + 3× retry with back-off
│   ├── models.py                # Pydantic models for extraction response
│   ├── normalizer.py            # Unit/date normalization
│   ├── inserter.py              # Idempotent DB insertion into lab_results
│   └── pipeline.py              # process_report_with_gemini() orchestrator
│
├── rules/                       # Deterministic health rules engine
│   ├── definitions.py           # 13 rule functions (low Hb, high cholesterol, …)
│   ├── engine.py                # evaluate_rules(client, user_id) → List[AlertRecord]
│   ├── inserter.py              # persist_alerts() → idempotent DB write
│   └── models.py                # AlertRecord, RuleResult, Severity, EvidenceRef
│
├── services/                    # Shared services
│   ├── context/                 # Context builder for RAG
│   ├── embeddings/              # Embedding interfaces + SentenceTransformers
│   ├── preprocessing/           # Text cleaning & chunking
│   └── retrieval/               # Vector retrieval (pgvector, FAISS, mock)
│
├── prompts/                     # System prompts for LLM roles
├── scripts/                     # Developer utility scripts (not imported by production)
└── tests/                       # Unit test suite
```

---

## Setup

### 1. Environment Variables

Create a `.env` file in `src/backend/`:

```env
# Supabase (required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_REPORTS_BUCKET=medical-reports
SUPABASE_OCR_REPORTS_TABLE=medical_reports

# Gemini AI (required for extraction)
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

### 4. Database Setup

Run in your Supabase SQL editor in order:

```sql
-- 1. Base schema (tables: medical_reports, lab_results, alerts, alert_evidence)
--    Run: db/schema.sql

-- 2. RAG chunks
--    Run: db/migrations/001_add_report_chunks.sql

-- 3. Chunk metadata
--    Run: db/migrations/002_add_report_chunk_metadata.sql

-- 4. Async pipeline status tracking (makes ocr_text nullable, adds processing_status)
--    Run: db/migrations/003_add_processing_status.sql
```

### 5. Start the Server

```bash
cd src
PYTHONPATH=. uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

---

## API Endpoints

### Reports — Full Async Pipeline (Recommended)

**`POST /reports/ingest`**

Upload a PDF or image. OCR and Gemini extraction start automatically in the background.  
Returns **HTTP 202** immediately — the client does not wait for processing to finish.

```bash
curl -X POST http://localhost:8000/reports/ingest \
  -F "user_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "file=@/path/to/report.pdf"
```

Response:
```json
{
  "report_id": "a1b2c3d4-...",
  "storage_path": "550e8400-.../20260309T120000Z_abc_report.pdf",
  "public_url": "https://...",
  "processing_status": "pending",
  "message": "Report queued. Poll GET /reports/status/{report_id} for progress."
}
```

Pipeline stages stored in `medical_reports.processing_status`:

| Stage | Meaning |
|-------|---------|
| `pending` | Uploaded; OCR not yet started |
| `ocr_complete` | OCR text saved; Gemini extraction running |
| `done` | Lab results written to `lab_results` |
| `failed` | Error — see `processing_error` field |

---

**`GET /reports/status/{report_id}`**

Poll progress after calling `/ingest`.

```bash
curl http://localhost:8000/reports/status/a1b2c3d4-...
```

Response (while processing):
```json
{
  "report_id": "a1b2c3d4-...",
  "source_file_name": "report.pdf",
  "processing_status": "ocr_complete",
  "processing_error": null,
  "ocr_confidence": 94.3,
  "lab_results_count": null
}
```

Response (when done):
```json
{
  "report_id": "a1b2c3d4-...",
  "processing_status": "done",
  "ocr_confidence": 94.3,
  "lab_results_count": 14
}
```

---

### Reports — Synchronous Pipeline (Scripts / Testing)

**`POST /reports/process`**

Same pipeline (upload → OCR → Gemini), but blocks until fully complete. Gemini is **always** used — there is no regex fallback.

```bash
curl -X POST http://localhost:8000/reports/process \
  -F "user_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "file=@/path/to/report.pdf"
```

Response (on success):
```json
{
  "report_id": "...",
  "storage_path": "...",
  "public_url": "...",
  "processing_status": "done",
  "ocr_confidence": 92.1,
  "ocr_text_preview": "...",
  "gemini_extraction": { "inserted": 12, "skipped": 0 },
  "gemini_error": null
}
```

---

### Reports — Low-Level Step Endpoints

Use these when you need fine-grained control or want to retry a single stage.

| Endpoint | Purpose |
|----------|---------|
| `POST /reports/upload` | Upload to Supabase Storage only — no OCR, no DB row |
| `POST /reports/ocr` | Run OCR on an already-uploaded file and persist to `medical_reports` |
| `POST /reports/extract-labs-gemini` | Run Gemini extraction on a report that already has OCR text |

```bash
# Step 1 — Upload only
curl -X POST http://localhost:8000/reports/upload \
  -F "user_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "file=@/path/to/report.pdf"
# → {"path": "...", "public_url": "..."}

# Step 2 — OCR
curl -X POST http://localhost:8000/reports/ocr \
  -F "user_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "storage_path=<path from step 1>"
# → {"report_id": "...", "ocr_text": "...", "confidence": 92.5}

# Step 3 — Gemini extraction
curl -X POST http://localhost:8000/reports/extract-labs-gemini \
  -F "report_id=<report_id from step 2>"
# → {"inserted": 12, "skipped": 0, "extraction_log": {...}}
```

---

### Alerts

**`POST /alerts/evaluate/{user_id}`**

Run the deterministic rules engine for a user. Fetches their lab results, evaluates 13 health rules, and persists the results to the `alerts` and `alert_evidence` tables.  
The operation is **idempotent** — re-running replaces any previous alerts.

```bash
curl -X POST http://localhost:8000/alerts/evaluate/550e8400-e29b-41d4-a716-446655440000
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

**`GET /alerts/{user_id}`**

Fetch all stored alerts for a user from the database, including the evidence that triggered each one.

```bash
# With evidence (default)
curl http://localhost:8000/alerts/550e8400-e29b-41d4-a716-446655440000

# Without evidence
curl "http://localhost:8000/alerts/550e8400-e29b-41d4-a716-446655440000?include_evidence=false"
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
      "reason": "Hemoglobin 7.2 g/dL — critically low (< 8 g/dL)",
      "created_at": "2026-03-09T12:00:00+00:00",
      "evidence": [
        {
          "id": "...",
          "report_id": "...",
          "lab_result_id": "...",
          "ocr_text_snippet": "Hemoglobin  7.2  g/dL"
        }
      ]
    },
    {
      "id": "...",
      "severity": "medium",
      "reason": "Total Cholesterol 215 mg/dL — borderline high (200–240)",
      "created_at": "2026-03-09T12:00:00+00:00",
      "evidence": [...]
    }
  ]
}
```

Severity values: `"low"` | `"medium"` | `"high"`

---

## OCR Module (`ocr/`)

### Preprocessing Pipeline

```
Image → grayscale → fastNlMeansDenoising (Non-Local Means) → adaptive threshold → deskew
```

| File | Key Function | Description |
|------|-------------|-------------|
| `preprocessor.py` | `preprocess_image(img)` | Full image preprocessing chain |
| `ocr_engine.py` | `run_ocr(img)` | Tesseract OCR → `(text, confidence)` |

---

## Gemini Extraction (`extraction/`)

### How It Works

1. **Fetch OCR text** — reads `ocr_text` from the `medical_reports` row
2. **Prompt Gemini** — structured prompt with strict rules: preserve exact values, extract every test, `null` for uncertainty, no interpretation
3. **Model**: `gemini-3.1-pro-preview` (configurable via `GEMINI_MODEL` env var)
4. **Retry logic**: same model, up to 3 attempts, exponential back-off (`2s → 4s → 8s`). No multi-model fallback.
5. **Normalize** — units to canonical forms, dates to ISO-8601
6. **Idempotent insert** — deletes previous `lab_results` for the report before inserting fresh rows

---

## Rules Engine (`rules/`)

13 deterministic rules evaluate lab result values and produce alerts:

| Rule ID | What it checks |
|---------|----------------|
| `low_hemoglobin` | Hb < 8 g/dL → HIGH; 8–12 → MEDIUM |
| `high_cholesterol` | Total cholesterol > 240 → HIGH; 200–240 → LOW |
| `high_ldl` | LDL > 190 → HIGH; 160–190 → MEDIUM |
| `high_blood_sugar` | Fasting glucose > 126 → HIGH; 100–126 → MEDIUM |
| `high_hba1c` | HbA1c ≥ 6.5% → HIGH; 5.7–6.5 → MEDIUM |
| `abnormal_tsh` | TSH > 10 or < 0.4 µIU/mL → HIGH/MEDIUM |
| `low_vitamin_d` | Vit D < 12 ng/mL → HIGH; 12–30 → MEDIUM |
| `low_b12` | B12 < 150 pg/mL → HIGH; 150–300 → MEDIUM |
| `high_creatinine` | Creatinine > 2.0 → HIGH; 1.3–2.0 → MEDIUM |
| `low_platelets` | Platelets < 50 → HIGH; 50–150 → MEDIUM |
| `abnormal_wbc` | WBC > 15 or < 2 → HIGH; 11–15 → MEDIUM |
| `any_abnormal` | ≥ 3 abnormal flags → HIGH; ≥ 1 → MEDIUM |
| `missing_critical_tests` | Missing both CBC and metabolic panels → LOW |

Rules are pure functions — no DB access, fully unit-testable without credentials.

---

## Database Tables

### `medical_reports`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | Report owner |
| `report_date` | DATE | Date of report (set by Gemini extraction) |
| `report_type` | TEXT | Report type (set by Gemini extraction) |
| `source_file_name` | TEXT | Original filename |
| `source_url` | TEXT | Supabase Storage URL |
| `ocr_text` | TEXT | Full OCR output (nullable until OCR completes) |
| `ocr_engine` | TEXT | `tesseract` |
| `ocr_confidence` | NUMERIC | Average Tesseract confidence (%) |
| `processing_status` | TEXT | `pending \| ocr_complete \| done \| failed` |
| `processing_error` | TEXT | Error message if `processing_status = 'failed'` |

### `lab_results`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `report_id` | UUID | FK → `medical_reports.id` |
| `test_name` | TEXT | Lab test name |
| `value` | NUMERIC | Numeric result (NULL if non-numeric) |
| `unit` | TEXT | Measurement unit |
| `reference_range` | TEXT | Normal range as printed |
| `abnormal_flag` | BOOLEAN | True if outside reference range |
| `extracted_from_page` | INT | Source page number |

> **Note:** `lab_results` has no `user_id`. To query lab results for a user:  
> `SELECT lr.* FROM lab_results lr JOIN medical_reports mr ON lr.report_id = mr.id WHERE mr.user_id = '<uuid>'`

### `alerts`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | Alert owner |
| `severity` | TEXT | `low \| medium \| high` |
| `reason` | TEXT | Human-readable explanation |
| `created_at` | TIMESTAMP | When the alert was generated |

### `alert_evidence`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `alert_id` | UUID | FK → `alerts.id` |
| `report_id` | UUID | FK → `medical_reports.id` |
| `lab_result_id` | UUID | FK → `lab_results.id` |
| `ocr_text_snippet` | TEXT | Raw text excerpt that triggered the alert |

---

## Key Design Decisions

1. **Async-first ingestion**: `POST /reports/ingest` returns a `report_id` immediately with HTTP 202. OCR and Gemini extraction run as a FastAPI `BackgroundTask` so multiple clients are processed in parallel.

2. **Gemini is the only extraction path**: The regex extraction endpoint (`/extract-labs`) has been removed. All lab data comes from Gemini AI.

3. **Idempotent operations**: Re-submitting a report or re-evaluating alerts always produces a clean slate — old rows are deleted before new ones are inserted.

4. **OCR text is immutable**: `medical_reports.ocr_text` is set exactly once by Tesseract and never modified. All downstream operations (Gemini, RAG indexing) read from it.

5. **Rules are pure**: Alert rules in `backend/rules/definitions.py` take only a user ID and a list of `LabRow` objects — no database access inside the rule functions. This makes them fully unit-testable without credentials.

6. **Status polling over webhooks**: Pipeline status is tracked as a column in `medical_reports` so the client can poll `GET /reports/status/{report_id}` without any additional infrastructure.

---

## Verification Scripts

Run from `src/`:

```bash
# OCR + Gemini full pipeline (end-to-end)
PYTHONPATH=. python backend/verify_reports.py

# Alerts rules engine (unit tests + DB integration)
PYTHONPATH=. python backend/scripts/alerts_test.py
```
