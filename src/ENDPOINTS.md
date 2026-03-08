# Backend API Endpoints

This document lists the backend API endpoints exposed by the FastAPI app in [src/backend/main.py](main.py).

Base URL (local): `http://localhost:8000`

---

## Health

### GET /health
Returns server health status.

**Response**
```json
{
  "status": "ok"
}
```

---

## Reports (Supabase Storage + OCR)

### POST /reports/upload
Uploads a medical report (PDF or image) to Supabase Storage.

**Form fields**
- `user_id` (string, UUID)
- `file` (file)

**Response**
```json
{
  "path": "<storage_path>",
  "public_url": "<public_url>"
}
```

**Notes**
- The file is stored in the Supabase bucket from `SUPABASE_REPORTS_BUCKET` (default: `medical-reports`).
- The storage path is required for OCR.

---

### POST /reports/ocr
Downloads the report from Supabase Storage, runs OCR, and inserts the extracted text into `medical_reports`.

**Form fields**
- `user_id` (string, UUID)
- `storage_path` (string)

**Response**
```json
{
  "path": "<storage_path>",
  "ocr_text": "<extracted_text>",
  "confidence": 92.5
}
```

**Database insert (medical_reports)**
- `id` (UUID)
- `user_id` (UUID)
- `source_file_name` (text)
- `source_url` (text)
- `ocr_text` (text)
- `ocr_engine` (text)
- `ocr_confidence` (numeric)

**Notes**
- Requires Tesseract and Poppler installed on the server.

---

## RAG Test (Mock)

### GET /api/v1/rag/test
Returns mock retrieval results for UI testing.

**Query params**
- `user_id` (string)
- `query` (string)

**Response**
Returns a mock JSON payload with `retrieved_chunks` and metadata.

---

## Standalone OCR Service (Optional)

The separate OCR-only API under `src/backend/ocr2` was a standalone prototype.
It has been **consolidated into `ocr/`** — the main backend includes all OCR functionality.

---

## Lab Extraction

### POST /reports/extract-labs
Extracts lab results from OCR text using **deterministic regex patterns** and inserts into `lab_results`.
This is the **primary** extraction method — no API key required, works offline.

**Form fields**
- `report_id` (string, UUID)

**Response**
```json
{
  "report_id": "<uuid>",
  "inserted": 12
}
```

---

### POST /reports/extract-labs-gemini
Extracts lab results from OCR text using **Google Gemini AI** and inserts into `lab_results`.
Optional enhancement — handles OCR noise and varied report formats. Requires a Gemini API key.

**Form fields**
- `report_id` (string, UUID)

**Response**
```json
{
  "report_id": "<uuid>",
  "inserted": 15,
  "skipped": 1,
  "metadata_updates": { "report_date": "2024-03-15", "report_type": "Complete Blood Count" },
  "extraction_log": { ... },
  "elapsed_seconds": 3.42
}
```

---

### POST /reports/process
**Full pipeline** — upload + OCR + regex extraction in one call. Optionally includes Gemini extraction.

**Form fields**
- `user_id` (string, UUID)
- `file` (file — PDF or image)
- `use_gemini` (boolean, optional — default `false`)

**Response**
```json
{
  "report_id": "<uuid>",
  "storage_path": "<path>",
  "public_url": "<url>",
  "ocr_confidence": 92.5,
  "ocr_text_preview": "...",
  "regex_extraction": { "inserted": 12, "error": null },
  "gemini_extraction": null,
  "gemini_error": null
}
```

---

## Environment Variables

Required for Supabase endpoints:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_REPORTS_BUCKET` (optional, defaults to `medical-reports`)
- `SUPABASE_OCR_REPORTS_TABLE` (optional, defaults to `medical_reports`)

Optional (for Gemini AI extraction):
- `GEMINI_API_KEY` — Google AI API key ([get one here](https://aistudio.google.com/app/apikey))
- `GEMINI_MODEL` (optional, defaults to `gemini-2.0-flash`)
