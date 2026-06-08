# Backend Setup and Run Guide

This backend is a FastAPI service inside the monorepo and is expected to be run from the src directory.

## 1. Prerequisites

- Python 3.10 or 3.11
- pip (latest)
- Supabase project (URL + service-role key)
- Google Gemini API key
- System binaries for OCR:
  - `tesseract-ocr`
  - `poppler-utils` (used by `pdf2image`)

On Ubuntu/Debian:

```bash
sudo apt update
sudo apt install -y python3-venv tesseract-ocr poppler-utils libgl1
```

`libgl1` helps avoid OpenCV runtime errors on some Linux environments.

## 2. Create a virtual environment

From repository root:

```bash
cd src/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Configure environment variables

Create `.env` inside `src/backend`.

Minimal required variables:

```env
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_SERVICE_ROLE_KEY=YOUR_SERVICE_ROLE_KEY
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

Recommended optional variables:

```env
# Storage/table config
SUPABASE_REPORTS_BUCKET=medical-reports
SUPABASE_OCR_REPORTS_TABLE=medical_reports

# Gemini config
GEMINI_MODEL=gemini-3.1-pro-preview
GEMINI_DATA_PROCESSING_APPROVED=false

# Retrieval tuning
RETRIEVAL_TOP_K=10
RETRIEVAL_MATCH_THRESHOLD=0.4

# Embedding config
EMBEDDING_MODEL_NAME=BAAI/bge-base-en-v1.5
EMBEDDING_NORMALIZE=true
EMBEDDING_VERSION=bge-base-en-v1.5-w3

# Voice route behavior
USE_AUDIO=false

# Optional for cron scripts
API_BASE_URL=http://localhost:8000
```

## 4. Database setup (Supabase)

- Enable extension `vector` in Supabase SQL editor/extensions.
- Run schema and migrations in order:

```bash
# From repository root
# 1) Apply base schema first
src/db/schema.sql

# 2) Apply migrations in lexical order from
src/db/migrations/
```

At minimum, run through `015_privacy_hardening.sql` so user/privacy and RLS paths match backend expectations.

## 5. Run the backend

Run from `src` (not from `src/backend`):

```bash
cd ../
uvicorn backend.main:app --reload --port 8000
```

Service URLs:

- API base: `http://localhost:8000`
- Health: `http://localhost:8000/health`
- Swagger docs: `http://localhost:8000/docs`

## 6. Quick validation checklist

- Open `/health` and confirm `{ "status": "ok" }`.
- Open `/docs` and ensure routes are visible.
- Test login/register flow first to validate Supabase connectivity.
- Test upload/ingest only after OCR dependencies and DB schema are ready.

## 7. Running tests

From `src/backend` with venv activated:

```bash
pytest -q
```

Some integration tests rely on configured Supabase/Gemini keys and populated data.

## 8. Common issues and fixes

1. `SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set`
- `.env` is missing or not loaded.
- Confirm `.env` exists in `src/backend` and variable names are exact.

2. `TesseractNotFoundError`
- Install `tesseract-ocr` and verify with `tesseract --version`.

3. `PDFInfoNotInstalledError` from `pdf2image`
- Install `poppler-utils` and verify `pdftoppm -v`.

4. OpenCV shared library errors (`libGL.so.1`)
- Install `libgl1`.

5. Gemini request/auth failures
- Check `GEMINI_API_KEY`.
- Optionally set `GEMINI_MODEL` to a valid model available in your account.

6. Upload/report processing works but retrieval is empty
- Ensure DB schema + migrations are applied.
- Ensure embeddings/indexing pipeline has run for the uploaded reports.

## 9. Notes for developers

- Keep secrets out of git. Do not commit `.env`.
- If you change table names/bucket names, update corresponding env vars.
- Run backend from `src` so imports like `backend.main:app` resolve consistently.
