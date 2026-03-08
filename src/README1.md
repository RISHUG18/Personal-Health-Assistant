# Week 2 — Structured Extraction & Database Ingestion

## Overview

This module turns raw OCR text from medical lab reports into **structured rows** in the database, following the frozen schema (`db/schema.sql`).

Two extraction paths are provided:
1. **OCR + Regex extraction** (primary) — deterministic, no API key needed, works offline
2. **Gemini AI extraction** (optional) — higher accuracy for messy OCR, requires a Google Gemini API key

---

## Architecture

```
PDF/Image
   │
   ▼
┌─────────────────────────┐
│  Upload to Supabase      │  POST /reports/upload
│  Storage                 │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Tesseract OCR           │  POST /reports/ocr
│  preprocessor →          │
│  ocr_engine              │
│  → medical_reports       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Regex Extraction        │  POST /reports/extract-labs    (PRIMARY)
│  (deterministic)         │
│  → lab_results           │
└─────────────────────────┘
            │
            ▼  (optional, if use_gemini=true)
┌─────────────────────────┐
│  Gemini AI Extraction    │  POST /reports/extract-labs-gemini
│  (LLM-based)            │
│  → lab_results           │
└─────────────────────────┘
```

Or use **POST /reports/process** to run the full pipeline in one call.

---

## Backend Folder Structure

```
backend/
├── main.py                      # FastAPI app entrypoint
├── requirements.txt             # Python dependencies
├── verify_reports.py            # End-to-end verification script
│
├── config/
│   └── supabase_client.py       # Supabase client configuration
│
├── controllers/
│   └── reports_controller.py    # Business logic (upload, OCR, extraction)
│
├── routes/
│   ├── reports.py               # HTTP routes for report operations
│   └── rag.py                   # RAG query pipeline routes
│
├── ocr/                         # Primary extraction module
│   ├── __init__.py              # Public API exports
│   ├── preprocessor.py          # Image preprocessing (grayscale, denoise, deskew)
│   ├── ocr_engine.py            # Tesseract OCR wrapper
│   ├── extractors.py            # Regex-based lab result extraction
│   ├── normalizers.py           # Unit/date/number normalization
│   ├── inserters.py             # DB insertion with abnormal flag computation
│   ├── pipeline.py              # End-to-end extraction orchestrator
│   └── README.md                # Module documentation
│
├── extraction/                  # Optional — Gemini AI extraction module
│   ├── __init__.py
│   ├── gemini_extractor.py      # Gemini API integration + prompt
│   ├── models.py                # Pydantic models for extraction
│   ├── normalizer.py            # AI-aware normalization
│   ├── inserter.py              # Idempotent DB insertion
│   └── pipeline.py              # Full extraction pipeline orchestration
│
├── services/                    # Shared services
│   ├── context/                 # Context builder for RAG
│   ├── embeddings/              # Embedding interfaces
│   ├── preprocessing/           # Text cleaning & chunking
│   └── retrieval/               # Vector retrieval (pgvector, FAISS)
│
├── prompts/                     # System prompts for LLM roles
├── scripts/                     # Utility scripts
└── tests/                       # Test suite
```

### What changed from Week 1

| Module | Status | Notes |
|--------|--------|-------|
| `ocr/preprocessor.py` | **NEW** | Image preprocessing (from `ocr2/` consolidation) |
| `ocr/ocr_engine.py` | **NEW** | Tesseract OCR wrapper (from `ocr2/` consolidation) |
| `ocr/extractors.py` | **UPDATED** | Regex extraction with 40+ test names |
| `ocr/normalizers.py` | **UPDATED** | Unit/date/number normalization |
| `ocr/inserters.py` | **UPDATED** | DB insertion with abnormal flag |
| `ocr/pipeline.py` | **UPDATED** | Orchestration entry point |
| `extraction/` | **NEW** | Gemini AI-based extraction (optional) |
| `controllers/reports_controller.py` | **UPDATED** | Added extraction functions |
| `routes/reports.py` | **UPDATED** | Added `/extract-labs`, `/extract-labs-gemini`, `/process` |

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

# Gemini AI (optional — only needed for /extract-labs-gemini)
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.0-flash
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

Run the schema and migrations in your Supabase SQL editor:

```sql
-- 1. Base schema
-- Run contents of db/schema.sql

-- 2. Report chunks for RAG
-- Run contents of db/migrations/001_add_report_chunks.sql

-- 3. Chunk metadata
-- Run contents of db/migrations/002_add_report_chunk_metadata.sql
```

### 5. Start the Server

```bash
cd src
PYTHONPATH=. uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: http://localhost:8000/docs

---

## API Endpoints

### Full Pipeline (Recommended)

**POST /reports/process**

Uploads a PDF/image, runs OCR, extracts lab data with regex, and inserts everything into the database — all in one call.

```bash
# Default: regex extraction only
curl -X POST http://localhost:8000/reports/process \
  -F "user_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "file=@/path/to/report.pdf"

# With optional Gemini extraction
curl -X POST http://localhost:8000/reports/process \
  -F "user_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "file=@/path/to/report.pdf" \
  -F "use_gemini=true"
```

### Step-by-Step

1. **Upload**: `POST /reports/upload`
2. **OCR**: `POST /reports/ocr`
3. **Extract (Regex)**: `POST /reports/extract-labs`
4. **Extract (Gemini)**: `POST /reports/extract-labs-gemini` *(optional)*

```bash
# Step 1: Upload
curl -X POST http://localhost:8000/reports/upload \
  -F "user_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "file=@/path/to/report.pdf"
# → {"path": "...", "public_url": "..."}

# Step 2: OCR
curl -X POST http://localhost:8000/reports/ocr \
  -F "user_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "storage_path=<path from step 1>"
# → {"report_id": "...", "ocr_text": "...", "confidence": 92.5}

# Step 3: Regex Extraction (primary)
curl -X POST http://localhost:8000/reports/extract-labs \
  -F "report_id=<report_id from step 2>"
# → {"report_id": "...", "inserted": 12}

# Step 4: Gemini Extraction (optional, requires API key)
curl -X POST http://localhost:8000/reports/extract-labs-gemini \
  -F "report_id=<report_id from step 2>"
# → {"inserted": 15, "skipped": 1, "extraction_log": {...}}
```

---

## OCR Module (`ocr/`)

The OCR module is the **primary extraction pipeline** — fully deterministic, no external API needed.

### Pipeline Flow

```
Image → preprocess_image() → run_ocr() → extract_lab_results() → insert_lab_results()
```

### Key Components

| File | Function | Description |
|------|----------|-------------|
| `preprocessor.py` | `preprocess_image(img)` | Grayscale → denoise → adaptive threshold → deskew |
| `ocr_engine.py` | `run_ocr(img)` | Tesseract OCR → (text, confidence) |
| `extractors.py` | `extract_lab_results(text)` | Regex parsing → `List[LabExtraction]` |
| `normalizers.py` | `normalize_unit()`, etc. | Unit/date/number normalization |
| `inserters.py` | `insert_lab_results(...)` | Insert into `lab_results` table |
| `pipeline.py` | `process_report_ocr(...)` | Orchestrates extract → insert |

### Extraction Rules
- **Allow-list based** — only recognized test names are extracted (40+ tests including CBC, lipids, liver, kidney, thyroid panels)
- **Numeric values only** — non-numeric results ("Positive", "Reactive") are skipped
- **Deterministic** — same input always produces same output
- **Safe** — no diagnosis or medical interpretation

### Usage

```python
# Standalone OCR (no server)
from backend.ocr import preprocess_image, run_ocr

# Full pipeline (with database)
from backend.ocr import process_report_ocr
rows = process_report_ocr(client, report_id, ocr_text)
```

---

## Gemini Extraction (`extraction/`) — Optional

When a Gemini API key is available, this module provides higher-accuracy extraction using LLM intelligence.

### How It Works

1. **Prompt Engineering** — strict rules: preserve exact values, extract every test, null for uncertainty, no interpretation
2. **Normalization** — units to canonical forms, dates to ISO-8601
3. **Idempotent Insertion** — deletes old `lab_results` for the report before re-inserting
4. **Logging** — detailed extraction log with counts, skipped items, and errors

### When to Use Gemini
- Reports with heavy OCR noise
- Non-standard report layouts
- Need to extract ALL tests (not just the allow-list)
- Need metadata extraction (report date, report type)

### Limitations
- Requires a Google Gemini API key (free tier may have quota limits)
- Not available in all regions (some regions have `limit: 0` on free tier)
- Get a key at: https://aistudio.google.com/app/apikey

---

## Database Tables

### `medical_reports` (stores raw OCR text — immutable)

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | Report owner |
| `report_date` | DATE | Date of the report (populated by Gemini if used) |
| `report_type` | TEXT | Type of report (populated by Gemini if used) |
| `source_file_name` | TEXT | Original filename |
| `source_url` | TEXT | Supabase storage URL |
| `ocr_text` | TEXT | Full OCR output (immutable) |
| `ocr_engine` | TEXT | Engine used (tesseract) |
| `ocr_confidence` | NUMERIC | Average OCR confidence |

### `lab_results` (structured values extracted from OCR)

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `report_id` | UUID | FK → medical_reports |
| `test_name` | TEXT | Lab test name |
| `value` | NUMERIC | Numeric result (NULL for non-numeric) |
| `unit` | TEXT | Measurement unit |
| `reference_range` | TEXT | Normal range as shown |
| `abnormal_flag` | BOOLEAN | True if out of range |
| `extracted_from_page` | INT | Source page number |

---

## Verification

### Standalone OCR test (no server, no Supabase)

```bash
cd src/backend
PYTHONPATH=.. python test_ocr.py
```

### Full pipeline verification

```bash
cd src
REPORT_FILE=backend/path/to/report.pdf USER_ID=$(uuidgen) \
  PYTHONPATH=. python backend/verify_reports.py
```

### Testing with multiple PDFs

```bash
export USER_ID=$(uuidgen)

REPORT_FILE=./reports/cbc_report.pdf python backend/verify_reports.py full
REPORT_FILE=./reports/lipid_panel.pdf python backend/verify_reports.py full
REPORT_FILE=./reports/metabolic_panel.pdf python backend/verify_reports.py full
```

---

## Key Design Decisions

1. **Regex as Primary, Gemini as Enhancement**: Regex extraction works offline, needs no API key, and is fully deterministic. Gemini is available as an optional upgrade for messy reports.

2. **Idempotent Insertion**: Re-processing a report deletes old `lab_results` and inserts fresh ones. No duplication.

3. **Non-Numeric Results**: Values like "Positive", "Negative" are stored with `value = NULL` (DB column is `NUMERIC`). The raw OCR text in `medical_reports` preserves everything.

4. **Schema Frozen**: No changes to `db/schema.sql`. All functionality works within the existing table structure.

5. **OCR Text Immutable**: The raw OCR text in `medical_reports.ocr_text` is never modified. Extraction and normalization happen downstream.

6. **`ocr2/` Consolidated**: The standalone prototype (`ocr2/`) has been consolidated into `ocr/` — `preprocessor.py` and `ocr_engine.py` were moved, the rest was discarded.
