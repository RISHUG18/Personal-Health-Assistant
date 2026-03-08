"""LLM-based structured extraction from medical reports using Google Gemini.

This module replaces regex-based extraction with Gemini AI for:
- Superior handling of OCR noise and varied report formats
- Complete extraction of all lab test results
- Intelligent date and metadata parsing

Public API:
    process_report_with_gemini(client, report_id) -> dict
"""

from backend.extraction.pipeline import process_report_with_gemini

__all__ = ["process_report_with_gemini"]
