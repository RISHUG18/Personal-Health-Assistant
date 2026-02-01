# OCR Service (ocr2)

## Overview
This module provides a FastAPI-based OCR service for medical reports. It accepts images or PDFs, preprocesses them, runs OCR, and (optionally) extracts structured medical data.

## Does this use Tesseract?
Yes. OCR is performed with Tesseract via the `pytesseract` library (see [ocr_engine.py](ocr_engine.py)).

## How it works
1. **Upload** a report file (image or PDF). The service stores it and returns a `report_id`.
2. **Run OCR** using the `report_id`. For PDFs, each page is converted to an image before OCR.
3. **Extract medical data** (optional) from the OCR text.

Pipeline summary:
- **Input**: image (JPG/PNG/etc.) or PDF
- **Preprocess**: `preprocess_image` (OpenCV + NumPy)
- **OCR**: Tesseract via `pytesseract`
- **Output**: full text + average confidence

## API usage (required order)
**Important**: You must upload first to get an ID, then run OCR using that ID.

1) Upload report
- Endpoint: `POST /upload-report`
- Returns: `{ "id": "<report_id>" }`

2) Run OCR
- Endpoint: `POST /run-ocr/{report_id}`
- Returns: plain text OCR output

3) Extract medical data (optional)
- Endpoint: `POST /extract-medical-data/{report_id}`
- Returns: structured JSON

## Running locally
1. Install Python dependencies:
   - `pip install -r requirements.txt`
2. Run the API:
   - `python main.py`
   - or `uvicorn main:app --reload`

## System dependencies
- **Tesseract OCR** must be installed on the system for `pytesseract` to work.
- **Poppler** is required for PDF support (`pdf2image`).

## Notes
- Storage is **in-memory** and **file-based** in `storage/` for demo purposes. IDs are not persisted across restarts.
- Supported inputs: images and PDFs.
