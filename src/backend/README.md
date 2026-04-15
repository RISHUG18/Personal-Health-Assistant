# Backend Overview

Brief notes on the current backend layout and what each file does.

The backend is structured as a Python package (use `backend.*` imports).

## Structure
- `__init__.py`: Marks `backend/` as a Python package.
- `main.py`: FastAPI entrypoint; initializes the app, healthcheck, and mounts routers.
- `requirements.txt`: Python dependencies for the backend (FastAPI, uvicorn, Supabase client, multipart support, dotenv, etc.).
- `mock_server.py`: Standalone mock backend for UI development (separate from the main API).
- `verify_reports.py`: Helper utility for validating report/OCR flows (as implemented).

### config/
- `config/__init__.py`: Package marker.
- `config/supabase_client.py`: Creates a singleton Supabase client from env vars and exposes the reports bucket helper.

### controllers/
- `controllers/__init__.py`: Package marker.
- `controllers/reports_controller.py`: Use-case logic for uploading reports + running OCR + extracting labs (coordinates OCR + Supabase operations).

### middleware/
- `middleware/__init__.py`: Package marker (no middlewares yet).

### routes/
- `routes/__init__.py`: Package marker.
- `routes/reports.py`: HTTP routes for report upload, OCR, and lab extraction; delegates to controllers.

### services/
Reusable business/processing logic (no FastAPI coupling):

- `services/preprocessing/`
	- `text_cleaning.py`: Cleans noisy OCR output into meaningful lines.
	- `chunking.py`: Splits cleaned text into retrieval-ready chunks.

- `services/embeddings/`
	- `interfaces.py`: `Embedder` protocol (interface) for dependency inversion.
	- `sentence_transformer_embedder.py`: SentenceTransformers implementation.
	- `query_embedding.py`: Convenience helpers (`get_default_embedder`, `embed_query`, `embed_texts`).

- `services/retrieval/`
	- `mock_retrieval.py`: Retrieval stub used for early UI citation rendering.

Compatibility shims remain at:
- `services/text_cleaning.py`
- `services/chunking.py`
- `services/mock_retrieval.py`

### scripts/
Developer smoke tests/utilities (not imported by production code).

### tests/
Unit tests and fixtures.

### contracts/
Contract artifacts (e.g., context schema, API spec).

### prompts/
System prompts used by the LLM reasoning layer.

### ocr/ and ocr2/
OCR and deterministic extraction pipelines.

## Quick start
1) Install deps: `pip install -r requirements.txt`
2) Set env vars: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, optional `SUPABASE_REPORTS_BUCKET` (defaults to `medical-reports`), `GEMINI_API_KEY`.
3) Apply DB migration: 
   - **Prerequisite:** You *must* enable the `vector` extension in your Supabase dashboard (Database -> Extensions -> `vector`).
   - Run `src/db/schema.sql` to establish base tables.
   - Run the migration sequence in `src/db/migrations/` sequentially up to at least `015_privacy_hardening.sql`.
4) Run (from `src/`): `uvicorn backend.main:app --reload --port 8000`

## Report ingestion API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/reports/ingest` | **Recommended.** Upload PDF → auto OCR → auto Gemini extraction. Returns `202` immediately with a `report_id`; processing runs in background. |
| `GET`  | `/reports/status/{report_id}` | Poll pipeline status: `pending → ocr_complete → done / failed`. |
| `POST` | `/reports/process` | Same pipeline but **blocking** — waits for OCR + Gemini before returning `201`. Useful for scripts/tests. |
| `POST` | `/reports/upload` | Storage upload only (no OCR). Low-level. |
| `POST` | `/reports/ocr` | OCR an already-uploaded file. Low-level. |
| `POST` | `/reports/extract-labs-gemini` | Run Gemini extraction on a report that already has OCR text. |

### Async ingest flow

```bash
# 1. Submit — returns immediately
curl -X POST \
  -F "user_id=<uuid>" \
  -F "file=@report.pdf" \
  http://localhost:8000/reports/ingest
# → {"report_id": "...", "processing_status": "pending", ...}

# 2. Poll until done
curl http://localhost:8000/reports/status/<report_id>
# → {"processing_status": "done", "lab_results_count": 12, ...}
```

Multiple clients can submit concurrently — each upload triggers an independent background job, so OCR + Gemini run in parallel across requests.

## Developer scripts

Run from `src/`:
- `python -m backend.scripts.rag_cleaning_smoke_test`
- `python -m backend.scripts.embedding_smoke_test`
