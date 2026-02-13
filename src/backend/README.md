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
2) Set env vars: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, optional `SUPABASE_REPORTS_BUCKET` (defaults to `medical-reports`).
3) Run (from `src/`): `uvicorn backend.main:app --reload --port 8000`
4) Test upload: use Swagger UI at `/docs` or `curl -F "user_id=123" -F "file=@/path/to/report.pdf" http://localhost:8000/reports/upload`

## PDF upload
1) Ensure env vars are set (or .env present) so Supabase client can connect.
2) Start the API from the `src/` folder: `uvicorn backend.main:app --reload --port 8000`.
3) Upload a report via either:
	 - Swagger UI: open `http://localhost:8000/docs`, expand `POST /reports/upload`, provide `user_id` and choose a file.
	 - Curl:
		 ```bash
		 curl -X POST \
			 -F "user_id=YOUR_USER_ID" \
			 -F "file=@/full/path/to/report.pdf" \
			 http://localhost:8000/reports/upload
		 ```
4) Uploaded files land in Supabase Storage under `reports/<user_id>/<timestamp>_<uuid>_<filename>` inside your bucket (defaults to `medical-reports`).

## Developer scripts

Run from `src/`:
- `python -m backend.scripts.rag_cleaning_smoke_test`
- `python -m backend.scripts.embedding_smoke_test`
