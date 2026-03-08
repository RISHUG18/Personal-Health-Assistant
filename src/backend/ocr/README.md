# OCR Processing Pipeline

This module provides the **complete OCR pipeline** for medical lab reports: image preprocessing → Tesseract OCR → structured lab result extraction → database insertion.

## Pipeline Flow

```
PDF/Image
   │
   ▼
┌────────────────────────────┐
│  preprocessor.preprocess_  │  Grayscale → Denoise → Threshold → Deskew
│  image(image)              │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  ocr_engine.run_ocr(img)   │  Tesseract → (text, confidence)
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  extractors.extract_lab_   │  Regex patterns → List[LabExtraction]
│  results(ocr_text)         │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  inserters.insert_lab_     │  → lab_results table (Supabase)
│  results(client, ...)      │
└────────────────────────────┘
```

## Guarantees
- Regex-only extraction (deterministic, no LLM)
- No AI/LLM inference — no diagnosis or interpretation
- OCR text stored in `medical_reports.ocr_text` is **never modified**
- Abnormal flag computed **only** from numeric comparison with reference range

## What is extracted
- `test_name` — from an explicit allow-list of known lab tests
- `value` — numeric value only (non-numeric results are skipped)
- `unit` — normalized to canonical form (e.g., `g/dl` → `g/dL`)
- `reference_range` — raw text, trimmed
- `extracted_from_page` — page number if present in OCR text

## Safety rules
- Extraction only if: test name is in the allow-list, value is numeric, and unit is recognized
- Partial/ambiguous matches are silently discarded
- Unknown units → result is skipped

## Files
| File | Purpose |
|------|---------|
| [preprocessor.py](preprocessor.py) | Image preprocessing (grayscale, denoise, adaptive threshold, deskew) |
| [ocr_engine.py](ocr_engine.py) | Tesseract OCR wrapper — returns (text, avg_confidence) |
| [extractors.py](extractors.py) | Regex-based lab result parsing from OCR text |
| [normalizers.py](normalizers.py) | Unit/date/number normalization helpers |
| [inserters.py](inserters.py) | Inserts extracted results into `lab_results` table |
| [pipeline.py](pipeline.py) | End-to-end orchestrator: extract → normalize → insert |

## Usage

### Standalone OCR (no server needed)
```python
from pdf2image import convert_from_path
import numpy as np
from backend.ocr import preprocess_image, run_ocr

pages = convert_from_path("report.pdf")
for page in pages:
    img = np.array(page)[:, :, ::-1].copy()  # PIL → OpenCV BGR
    processed = preprocess_image(img)
    text, confidence = run_ocr(processed)
    print(f"Confidence: {confidence:.1f}%")
    print(text)
```

### Full extraction pipeline (with database)
```python
from backend.config.supabase_client import get_supabase_client
from backend.ocr import process_report_ocr

client = get_supabase_client()
rows = process_report_ocr(client, report_id="<uuid>", ocr_text=raw_ocr_text)
print(f"Inserted {rows} lab results")
```

### Via API endpoint
```bash
# Regex extraction from an already-OCR'd report
curl -X POST http://localhost:8000/reports/extract-labs \
  -F "report_id=<uuid>"
```

## Notes
- To expand recognized tests, update `_TEST_NAMES` in [extractors.py](extractors.py)
- Units are **normalized** but **never converted** (e.g., mg/dL stays mg/dL)
- For higher accuracy on messy OCR text, use the Gemini-based extraction in `extraction/` (requires API key)
