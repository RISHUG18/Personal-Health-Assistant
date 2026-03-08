# Week 2 — OCR, Gemini Extraction & Supabase Ingestion

## Overview

This module turns a raw PDF medical lab report into **structured rows in Supabase** through a fully automated pipeline:

```
PDF  →  Supabase Storage  →  Tesseract OCR  →  Gemini AI Extraction  →  lab_results (DB)
```

Two extraction paths are available:

| Path | Endpoint | When to use |
|---|---|---|
| **Regex** (primary) | `POST /reports/extract-labs` | Offline / no API key / deterministic |
| **Gemini AI** (recommended) | `POST /reports/extract-labs-gemini` | All reports — handles OCR noise, any layout |

The single **`POST /reports/process`** endpoint runs the entire pipeline (upload → OCR → regex → Gemini) in one call.

---

## Architecture

```
PDF / Image File
       │
       ▼
┌──────────────────────────┐
│  Upload to Supabase       │  POST /reports/upload
│  Storage (medical-reports │
│  bucket)                  │
└────────────┬─────────────┘
             │  storage_path
             ▼
┌──────────────────────────┐
│  Tesseract OCR            │  POST /reports/ocr
│  preprocessor.py          │  ├─ grayscale + denoise
│  → ocr_engine.py          │  ├─ adaptive threshold
│  → medical_reports (DB)   │  └─ deskew + Tesseract
└────────────┬─────────────┘
             │  report_id + ocr_text
             ▼
┌──────────────────────────┐
│  Regex Extraction         │  POST /reports/extract-labs
│  ocr/extractors.py        │  Deterministic, allow-list,
│  → lab_results (DB)       │  40+ test names recognised
└────────────┬─────────────┘
             │  (runs in same request when use_gemini=true)
             ▼
┌──────────────────────────┐
│  Gemini AI Extraction     │  POST /reports/extract-labs-gemini
│  extraction/pipeline.py   │  LLM reads raw OCR text,
│  Model: gemini-2.5-flash  │  returns every test verbatim
│  → lab_results (DB)       │  (idempotent — replaces regex rows)
└──────────────────────────┘
```

> **Idempotent** — calling Gemini extraction on the same `report_id` deletes old `lab_results` rows and re-inserts fresh ones. No duplicates.

---

## Folder Structure

```
backend/
├── main.py                        # FastAPI app entrypoint
├── requirements.txt               # Python dependencies
│
├── config/
│   └── supabase_client.py         # Supabase client + env var helpers
│
├── controllers/
│   └── reports_controller.py      # Business logic (upload, OCR, extraction)
│
├── routes/
│   ├── reports.py                 # HTTP routes: /reports/*
│   └── rag.py                     # RAG query routes
│
├── ocr/                           # Regex-based extraction (primary, offline)
│   ├── preprocessor.py            # Image preprocessing (grayscale → deskew)
│   ├── ocr_engine.py              # Tesseract OCR wrapper → (text, confidence)
│   ├── extractors.py              # Regex parsing → List[LabExtraction]
│   ├── normalizers.py             # Unit/date/number normalization
│   ├── inserters.py               # DB insertion with abnormal flag logic
│   └── pipeline.py                # Orchestrator: extract → insert
│
├── extraction/                    # Gemini AI-based extraction (recommended)
│   ├── gemini_extractor.py        # Gemini API client + hardened system prompt
│   ├── models.py                  # Pydantic models for extraction I/O
│   ├── normalizer.py              # Post-Gemini normalization (units, dates)
│   ├── inserter.py                # Idempotent DB inserter (delete + re-insert)
│   └── pipeline.py                # Full orchestration: fetch → extract → insert → log
│
├── services/
│   ├── context/                   # Context builder for RAG
│   ├── embeddings/                # Embedding interfaces
│   ├── preprocessing/             # Text cleaning & chunking
│   └── retrieval/                 # Vector retrieval (pgvector / FAISS)
│
├── prompts/                       # System prompts for LLM roles
├── scripts/                       # Utility / ingestion scripts
└── tests/                         # Unit test suite
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

# Gemini AI (required for Gemini extraction)
GEMINI_API_KEY=your-gemini-api-key
# Optional: override model (default is gemini-2.5-flash)
# GEMINI_MODEL=gemini-2.5-flash
```

Get a Gemini API key for free at: https://aistudio.google.com/app/apikey

### 2. System Dependencies

```bash
# Ubuntu / Debian
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

Run in your Supabase SQL editor (in order):

```sql
-- 1. Base schema (medical_reports, lab_results, alerts, alert_evidence)
-- Paste contents of: db/schema.sql

-- 2. Report chunks for RAG
-- Paste contents of: db/migrations/001_add_report_chunks.sql

-- 3. Chunk metadata
-- Paste contents of: db/migrations/002_add_report_chunk_metadata.sql
```

### 5. Start the Server

```bash
cd src
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

API documentation (Swagger UI): http://localhost:8000/docs  
Health check: http://localhost:8000/health

---

## API Reference

### `POST /reports/process` — Full pipeline in one call ✅ Recommended

Uploads a PDF/image, runs OCR, runs regex extraction, and optionally runs Gemini AI extraction — all in a single HTTP request.

**Form fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `user_id` | UUID string | ✅ | Owner of the report |
| `file` | file upload | ✅ | PDF or image file |
| `use_gemini` | boolean | ❌ (default `false`) | Set `true` to also run Gemini extraction |

**Request — regex only:**

```bash
curl -X POST http://localhost:8000/reports/process \
  -F "user_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "file=@/path/to/report.pdf"
```

**Request — with Gemini extraction (recommended):**

```bash
curl -X POST http://localhost:8000/reports/process \
  -F "user_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "file=@/path/to/report.pdf" \
  -F "use_gemini=true"
```

**Response:**

```json
{
  "report_id": "6889dcfa-e955-4b26-b1c7-f3521a995f05",
  "storage_path": "550e8400.../20260308T152428Z_abc123_report.pdf",
  "public_url": "https://xxx.supabase.co/storage/v1/object/public/...",
  "ocr_confidence": 83.87,
  "ocr_text_preview": "--- Page 1 ---\nName: John Doe  Lab No: ...",
  "regex_extraction": {
    "inserted": 0,
    "error": null
  },
  "gemini_extraction": {
    "report_id": "6889dcfa-...",
    "source_file": "report.pdf",
    "inserted": 7,
    "skipped": 0,
    "metadata_updates": {
      "report_date": "2025-12-27",
      "report_type": "Test Report"
    },
    "extraction_log": {
      "total_tests_found": 7,
      "tests_inserted": 7,
      "tests_skipped": 0,
      "warnings": [],
      "errors": []
    },
    "gemini_notes": null,
    "elapsed_seconds": 14.49
  },
  "gemini_error": null
}
```

---

### `POST /reports/upload` — Upload only

Uploads a file to Supabase Storage and returns the storage path. Does not run OCR.

```bash
curl -X POST http://localhost:8000/reports/upload \
  -F "user_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "file=@/path/to/report.pdf"
```

```json
{
  "path": "550e8400-.../20260308T...abc_report.pdf",
  "public_url": "https://xxx.supabase.co/storage/v1/object/public/..."
}
```

---

### `POST /reports/ocr` — OCR only

Downloads a previously uploaded report from storage, runs Tesseract OCR, persists a row in `medical_reports`, and returns the OCR text.

```bash
curl -X POST http://localhost:8000/reports/ocr \
  -F "user_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "storage_path=550e8400-.../20260308T...abc_report.pdf"
```

```json
{
  "path": "550e8400-.../20260308T...abc_report.pdf",
  "ocr_text": "--- Page 1 ---\nName: John Doe ...",
  "confidence": 83.87,
  "report_id": "6889dcfa-e955-4b26-b1c7-f3521a995f05"
}
```

---

### `POST /reports/extract-labs` — Regex extraction

Fetches OCR text for an existing `report_id` and runs the deterministic regex extractor. Works offline, no API key needed.

```bash
curl -X POST http://localhost:8000/reports/extract-labs \
  -F "report_id=6889dcfa-e955-4b26-b1c7-f3521a995f05"
```

```json
{
  "report_id": "6889dcfa-e955-4b26-b1c7-f3521a995f05",
  "inserted": 5
}
```

---

### `POST /reports/extract-labs-gemini` — Gemini AI extraction

Fetches OCR text for an existing `report_id`, sends it to Gemini, and inserts every extracted lab result into `lab_results`. Idempotent — re-running replaces old rows.

```bash
curl -X POST http://localhost:8000/reports/extract-labs-gemini \
  -F "report_id=6889dcfa-e955-4b26-b1c7-f3521a995f05"
```

```json
{
  "report_id": "6889dcfa-e955-4b26-b1c7-f3521a995f05",
  "source_file": "document-2.pdf",
  "inserted": 7,
  "skipped": 0,
  "metadata_updates": {
    "report_date": "2025-12-27",
    "report_type": "Test Report"
  },
  "extraction_log": {
    "total_tests_found": 7,
    "tests_inserted": 7,
    "tests_skipped": 0,
    "warnings": [],
    "errors": []
  },
  "gemini_notes": null,
  "elapsed_seconds": 14.49
}
```

---

## Gemini Extraction Details (`extraction/`)

### Model & Fallback Chain

| Priority | Model | Notes |
|---|---|---|
| 1 (primary) | `gemini-2.5-flash` | Confirmed working, default |
| 2 | `gemini-3-flash-preview` | Fast when available, often 503 |
| 3 | `gemini-2.5-flash-lite` | Lighter fallback |
| 4 | `gemini-2.0-flash-lite` | Last resort |

- **429 (quota blocked)** — skips to next model immediately  
- **503 (overloaded)** — skips to next model immediately  
- Override primary model: set `GEMINI_MODEL=gemini-2.5-flash` in `.env`

### Prompt Design — Copy-Paste Fidelity

The system prompt enforces strict read-only extraction. The LLM is **explicitly prohibited** from:

- Rounding or altering any number
- Converting or normalizing units
- Computing derived values not present in the report
- Adding medical interpretation or diagnosis
- Filling in missing fields by inference

The LLM **may only**:
- Transcribe values character-for-character from the source text
- Correct obvious OCR misspellings in test *names* only (e.g. `"Hernoglobin"` → `"Hemoglobin"`)
- Set `is_abnormal` from explicit markers only (`H`, `L`, `*`, `↑`, `↓`)

### Post-Extraction Normalization

After Gemini returns JSON, `normalizer.py` applies:
- Units → canonical form (`"g/dl"` → `"g/dL"`, `"10^3/ul"` → `"10³/µL"`)
- Dates → ISO-8601 `YYYY-MM-DD`
- Test names → trim and collapse whitespace

### Inserter Behaviour

- Deletes all existing `lab_results` rows for the `report_id` before inserting (idempotent)
- Abnormal flag priority: Gemini flag → numeric range check → `null`
- Skips rows with empty `test_name` or both `value` and `value_string` empty
- Updates `medical_reports.report_date` and `report_type` from extracted metadata

---

## Database Tables

### `medical_reports`

| Column | Type | Description |
|---|---|---|
| `id` | UUID PK | Primary key |
| `user_id` | UUID | Report owner |
| `report_date` | DATE | Date on the report (set by Gemini) |
| `report_type` | TEXT | e.g. "Test Report", "CBC" (set by Gemini) |
| `source_file_name` | TEXT | Original filename |
| `source_url` | TEXT | Supabase public storage URL |
| `ocr_text` | TEXT | Full raw OCR output — **never modified** |
| `ocr_engine` | TEXT | `"tesseract"` |
| `ocr_confidence` | NUMERIC | Average Tesseract confidence (0–100) |
| `created_at` | TIMESTAMP | Row creation time |

### `lab_results`

| Column | Type | Description |
|---|---|---|
| `id` | UUID PK | Primary key |
| `report_id` | UUID FK | → `medical_reports.id` (CASCADE DELETE) |
| `test_name` | TEXT NOT NULL | Lab test name |
| `value` | NUMERIC | Numeric result (`NULL` for non-numeric results) |
| `unit` | TEXT | Unit exactly as extracted |
| `reference_range` | TEXT | Normal range as printed on the report |
| `abnormal_flag` | BOOLEAN | `true` = out of range, `false` = normal, `null` = unknown |
| `extracted_from_page` | INT | Page number the result was found on |

---

## Real Test Run — `document-2.pdf`

Verified run on 2026-03-08. Patient: Rishabh Goyal, Collected 27/12/2025 at LPL Dwarka-2.

| Metric | Value |
|---|---|
| Total pipeline time | **41.8s** |
| Gemini extraction time | **14.5s** |
| OCR confidence | **83.87%** |
| OCR text extracted | **10,467 characters** |
| Gemini model used | `gemini-2.5-flash` |
| Lab results inserted | **7** |
| Abnormal results | **3** |

**Lab results stored in `lab_results`:**

| # | Test Name | Value | Unit | Reference Range | Abnormal | Page |
|---|---|---|---|---|---|---|
| 1 | HEMOGLOBIN (Hb) ESTIMATION | 14.6 | g/dL | 13.00 – 17.00 | No | 1 |
| 2 | VITAMIN B12 (CYANOCOBALAMIN) | 118.0 | pg/mL | 211.00 – 946.00 | **YES** | 1 |
| 3 | VITAMIN D 25 - HYDROXY | 26.5 | nmol/L | 75.00 – 250.00 | **YES** | 1 |
| 4 | Ferritin | 137.0 | ng/mL | 30 – 400 | No | 3 |
| 5 | T3, Total | 1.34 | ng/mL | 0.91 – 2.18 | No | 3 |
| 6 | T4, Total | 8.14 | ug/dL | 5.91 – 13.20 | No | 3 |
| 7 | TSH | 4.7 | µIU/mL | 0.51 – 4.30 | **YES** | 3 |

**Metadata updated in `medical_reports`:**
- `report_date` = `2025-12-27`
- `report_type` = `Test Report`

---

## Using the Pipeline from Python

### Programmatic (no HTTP server needed)

```python
import os
from dotenv import load_dotenv
from supabase import create_client
from backend.extraction.pipeline import process_report_with_gemini

load_dotenv("src/backend/.env")
client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
)

# report_id must already exist in medical_reports (created by the OCR step)
result = process_report_with_gemini(client=client, report_id="<uuid>")

print(f"Inserted: {result['inserted']}")
print(f"Report date: {result['metadata_updates'].get('report_date')}")
for log_entry in result["extraction_log"]["warnings"]:
    print(f"Warning: {log_entry}")
```

### Via HTTP (curl / Android / any client)

```python
import requests

BASE_URL = "http://localhost:8000"

# Single call: upload + OCR + Gemini extraction
with open("report.pdf", "rb") as f:
    resp = requests.post(
        f"{BASE_URL}/reports/process",
        data={
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "use_gemini": "true",
        },
        files={"file": ("report.pdf", f, "application/pdf")},
        timeout=300,
    )

result = resp.json()
report_id    = result["report_id"]
gemini       = result["gemini_extraction"] or {}
inserted     = gemini.get("inserted", 0)
report_date  = (gemini.get("metadata_updates") or {}).get("report_date")

print(f"report_id={report_id}")
print(f"{inserted} lab results stored in Supabase")
print(f"Report date: {report_date}")
```

---

## Key Design Decisions

1. **Gemini as recommended extractor** — `gemini-2.5-flash` handles any report layout, any OCR noise level, without a fixed allow-list. Regex extraction still runs first as an offline fallback.

2. **Copy-paste fidelity prompt** — The LLM is a read-only extraction engine. It cannot round values, convert units, infer missing data, or add medical interpretation. Forbidden actions are explicitly listed in the system prompt.

3. **Idempotent insertion** — Re-processing a report clears old `lab_results` rows before inserting new ones. Safe to call multiple times.

4. **Automatic model fallback** — If the primary model is quota-blocked (429) or overloaded (503), the extractor silently tries the next model in the chain without raising an error.

5. **OCR text is immutable** — `medical_reports.ocr_text` is written once and never modified. All downstream extraction and normalization work from that fixed snapshot.

6. **Non-numeric results** — Values like `Positive`, `Negative`, `Reactive` are stored with `value = NULL` (the DB column is `NUMERIC`). The original word is preserved in the LLM's internal `value_string` for traceability.

7. **Schema frozen** — No changes to `db/schema.sql`. The entire pipeline works within the existing table structure.
