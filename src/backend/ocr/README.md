# Deterministic OCR Post-processing

This module extracts **only mechanically verifiable lab results** from immutable OCR text stored in `medical_reports.ocr_text`.

## Guarantees
- Regex-only extraction
- No AI/LLM inference
- No diagnosis/interpretation
- OCR text is never modified

## What is extracted
- `test_name`
- `value`
- `unit`
- `reference_range`
- `extracted_from_page` (if explicitly present)

## Safety rules
- Extraction happens only if: test name is recognized, value is numeric, and unit is present.
- Partial/ambiguous matches are discarded.
- Abnormal flag is computed **only** from numeric comparison with reference range.

## Files
- [extractors.py](extractors.py): Regex-only parsing logic
- [normalizers.py](normalizers.py): Unit/date/number normalization
- [inserters.py](inserters.py): Inserts into `lab_results`
- [pipeline.py](pipeline.py): Orchestration entry point

## Usage
```python
from config.supabase_client import get_supabase_client
from ocr.pipeline import process_report_ocr

client = get_supabase_client()
rows = process_report_ocr(client, report_id="<uuid>", ocr_text=raw_ocr_text)
print(rows)
```

## Notes
- Update `_TEST_NAMES` in [extractors.py](extractors.py) to expand allowed tests.
- Units are normalized, but **not converted**.
