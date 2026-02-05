# OCR Service (ocr2)

## Overview
This module provides a FastAPI-based OCR service for medical reports. It accepts images or PDFs, preprocesses them, runs OCR, and (optionally) extracts structured medical data.

OCR is currently implemented with a TrOCR model from Hugging Face (see [ocr_engine.py](ocr_engine.py)).

## Folder contents (files and purpose)
- [create_sample.py](create_sample.py): Generates a synthetic lab report image for quick OCR testing and demos.
- [extractor.py](extractor.py): Post-OCR extraction logic. Parses patient info and test results from raw OCR text and builds a `MedicalReport`.
- [main.py](main.py): FastAPI app with upload, OCR, and extraction endpoints. Manages temporary in-memory state and file storage in [storage/](storage/).
- [models.py](models.py): Pydantic models for structured output (`PatientInfo`, `TestResult`, `SourceMetadata`, `MedicalReport`).
- [ocr_engine.py](ocr_engine.py): OCR implementation using `microsoft/trocr-base-handwritten` via `transformers` + `torch`. Returns text and confidence.
- [preprocessor.py](preprocessor.py): Image preprocessing pipeline (grayscale, denoise, adaptive threshold, deskew).
- [requirements.txt](requirements.txt): Python dependencies for the OCR service.
- [verify.py](verify.py): Simple client script that exercises upload + OCR endpoints for manual verification.
- [storage/](storage/): Local file storage directory used by the demo service. Not persisted across restarts.

## How it works
1. **Upload** a report file (image or PDF). The service stores it and returns a `report_id`.
2. **Run OCR** using the `report_id`. For PDFs, each page is converted to an image before OCR.
3. **Extract medical data** (optional) from the OCR text.

Pipeline summary:
- **Input**: image (JPG/PNG/etc.) or PDF
- **Preprocess**: `preprocess_image` (OpenCV + NumPy)
- **OCR**: TrOCR via `transformers` + `torch`
- **Output**: full text + average confidence

## API usage (required order)
**Important**: You must upload first to get an ID, then run OCR using that ID.

1) Upload report
- Endpoint: `POST /upload-report`
- Returns: `{ "id": "<report_id>", "message": "File uploaded successfully" }`

2) Run OCR
- Endpoint: `POST /run-ocr/{report_id}`
- Returns: plain text OCR output

3) Extract medical data (optional)
- Endpoint: `POST /extract-medical-data/{report_id}`
- Returns: structured JSON (`MedicalReport`)

## Running locally
1. Install Python dependencies:
   - `pip install -r requirements.txt`
2. Run the API:
   - `python main.py`
   - or `uvicorn main:app --reload`

## System dependencies
- **Poppler** is required for PDF support (`pdf2image`).
- **GPU/CUDA** is optional but improves TrOCR performance if available.

## Notes
- Storage is **in-memory** and **file-based** in [storage/](storage/) for demo purposes. IDs are not persisted across restarts.
- Supported inputs: images and PDFs.

## Supabase integration (required changes)
The current implementation uses `reports_db` in memory and local file storage. To integrate with Supabase, replace these with persistent storage and metadata tables.

### 1) Add Supabase client
- Reuse existing Supabase config from [src/backend/config/supabase_client.py](../config/supabase_client.py).
- Import the client in [main.py](main.py) and use it for storage + database writes.

### 2) Store files in Supabase Storage
- Create a storage bucket (e.g., `medical-reports`).
- On upload, stream the uploaded file to Supabase Storage and persist the public or signed URL.
- Replace `STORAGE_DIR` and file system writes with Supabase Storage operations.

### 3) Persist report metadata in Supabase DB
Create a table (example: `ocr_reports`) to track status and results:
- `id` (uuid, primary key)
- `original_filename` (text)
- `storage_path` (text)
- `public_url` (text)
- `status` (text: uploaded|ocr_completed|extracted|error)
- `ocr_text` (text, nullable)
- `confidence` (float, nullable)
- `extracted_data` (jsonb, nullable)
- `created_at` (timestamp)

Update [main.py](main.py) endpoints to read/write status from the table instead of `reports_db`.

### 4) PDF processing with Supabase
- When processing PDFs, download the file from Supabase Storage to a temp path or bytes buffer before `pdf2image`.
- Ensure temp files are cleaned up after OCR.

### 5) Security & access
- Use signed URLs for private files instead of public URLs.
- Restrict bucket access and enforce row-level security (RLS) on the `ocr_reports` table.

### 6) Suggested code changes (summary)
- [main.py](main.py): replace `reports_db` and local file writes with Supabase DB + Storage operations.
- [verify.py](verify.py): optionally support uploading by passing a file from disk to the API as before (no changes required), but test that OCR results persist in Supabase.
- [requirements.txt](requirements.txt): add `supabase` (if not already present in the broader backend dependencies).

### 7) Optional improvements
- Add a `/reports/{report_id}` endpoint to fetch persisted OCR status and metadata from Supabase.
- Add retries for storage writes and error reporting with status updates.
