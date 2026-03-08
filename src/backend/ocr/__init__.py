"""OCR processing pipeline for medical lab reports.

This module handles the complete OCR pipeline:

Submodules:
    preprocessor    — Image preprocessing (grayscale, denoise, threshold, deskew)
    ocr_engine      — Tesseract OCR wrapper (text + confidence)
    extractors      — Regex-based lab result extraction from OCR text
    normalizers     — Unit, date, and numeric normalization helpers
    inserters       — Database insertion of extracted lab results
    pipeline        — End-to-end orchestrator (extract → normalize → insert)

Public API:
    preprocess_image(image) -> np.ndarray
    run_ocr(image) -> (text, confidence)
    process_report_ocr(client, report_id, ocr_text) -> int
"""

from backend.ocr.preprocessor import preprocess_image
from backend.ocr.ocr_engine import run_ocr
from backend.ocr.pipeline import process_report_ocr

__all__ = ["preprocess_image", "run_ocr", "process_report_ocr"]
