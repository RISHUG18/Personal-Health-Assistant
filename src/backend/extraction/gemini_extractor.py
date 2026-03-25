"""Google Gemini API integration for structured lab data extraction.

Sends OCR text to Gemini with a carefully designed prompt that instructs the
model to extract every lab result, preserve exact numeric values, and return
structured JSON.  The response is validated into Pydantic models.

Environment variables
---------------------
GEMINI_API_KEY : str
    Google AI API key (required).
GEMINI_MODEL : str
    Model name, defaults to ``gemini-2.0-flash``.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Optional

from google import genai
from google.genai import types

from .models import (
    ExtractedLabResult,
    ExtractedReportMetadata,
    GeminiExtractionResponse,
)

logger = logging.getLogger(__name__)

# ── Prompt ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a highly precise medical laboratory report data extraction system.
Your ONLY task is to parse the provided OCR text from a medical lab report
and extract every lab test result into structured JSON.

═══════════════════════════════════════════════════════════════════════════════
CRITICAL RULES — violating ANY of these is unacceptable
═══════════════════════════════════════════════════════════════════════════════

1. PRESERVE EXACT VALUES
   • Never round, truncate, or modify any numeric value.
   • If the report says "13.52", output exactly 13.52 — not 13.5, not 14.
   • If the report says "0.03", output 0.03 — not 0.0 or 0.
   • Decimal precision must match the source exactly.

2. EXTRACT EVERY TEST
   • Do NOT skip any test result, no matter how minor.
   • Include all sub-tests (e.g., every line of a Differential Count).
   • Include calculated values (e.g., LDL calculated, A/G ratio).
   • Include indices (MCV, MCH, MCHC, RDW, MPV, PDW, etc.).

3. NULL FOR UNCERTAINTY
   • If you are NOT confident about any field, set it to null.
   • Do NOT guess, infer, or fabricate values.
   • Better to return null than an incorrect value.

4. ORIGINAL UNITS
   • Report units EXACTLY as they appear in the text.
   • Do NOT convert between unit systems (e.g., do not convert mg/dL to mmol/L).
   • Preserve case: "g/dL" stays "g/dL", "mg/dL" stays "mg/dL".

5. REFERENCE RANGES
   • Extract the FULL reference range string as-is.
   • Examples: "12.0 - 16.0", "< 200", "> 40", "4.0 - 11.0 x10^3/µL"
   • If the range includes units, include them.
   • If no range is shown for a test, set to null.

6. ABNORMAL FLAGS
   • If the report marks a value as High (H), Low (L), Abnormal (*),
     out of range (↑ ↓), or with any abnormality indicator → is_abnormal = true.
   • If the value is explicitly within the reference range → is_abnormal = false.
   • If you cannot determine abnormality → is_abnormal = null.

7. DATE HANDLING
   • Extract report date and convert to YYYY-MM-DD format.
   • If the date format is ambiguous (e.g., 03/04/2024), prefer DD/MM/YYYY
     unless context clearly indicates otherwise.
   • If completely unclear, set to null.

8. PAGE TRACKING
   • OCR text may contain page markers like "--- Page 1 ---".
   • Track which page each result was found on.
   • If no page markers exist, set page_number to null.

9. OCR ERROR HANDLING
   • The text was extracted via Tesseract OCR and WILL contain artifacts:
     – Extra or missing spaces
     – Broken words across lines
     – Misread characters (0↔O, 1↔l, rn↔m, cl↔d)
   • You MAY correct obvious OCR errors in test NAMES ONLY
     (e.g., "Hernoglobin" → "Hemoglobin", "Platelet Coont" → "Platelet Count").
   • NEVER correct numeric values or units — extract them as-is.

10. NO INTERPRETATION
    • Do NOT add medical interpretation or diagnosis.
    • Do NOT compute values that are not in the report.
    • Do NOT create test results that are not present in the text.

═══════════════════════════════════════════════════════════════════════════════
OUTPUT SCHEMA (return ONLY valid JSON — no markdown fences, no commentary)
═══════════════════════════════════════════════════════════════════════════════

{
  "metadata": {
    "report_date": "YYYY-MM-DD or null",
    "report_type": "string describing report type, or null",
    "patient_name": "patient name or null",
    "lab_name": "laboratory name or null"
  },
  "lab_results": [
    {
      "test_name": "Full Test Name (OCR-corrected if needed)",
      "value": <number or null>,
      "value_string": "original string representation or null",
      "unit": "unit as shown or null",
      "reference_range": "range as shown or null",
      "is_abnormal": <true | false | null>,
      "page_number": <integer or null>
    }
  ],
  "extraction_notes": "Brief notes on any issues, ambiguities, or items that could not be extracted"
}

FIELD DETAILS:
• "value" → MUST be a JSON number (int or float) or null.
  For non-numeric results (Positive, Negative, Reactive, Non-Reactive, Present,
  Absent, etc.), set value to null and put the string in value_string.
• "value_string" → Raw string representation of the value.
  Always populate this alongside value for traceability.
• "test_name" → Use the full, standard medical name.
  Fix obvious OCR misspellings in the name only.
• "extraction_notes" → Describe any issues: missing data, illegible sections,
  ambiguous values, skipped items and why.
"""


def _clean_json_response(raw: str) -> str:
    """Strip markdown code fences or other wrappers from Gemini's response."""
    text = raw.strip()
    # Remove ```json ... ``` wrappers
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def extract_with_gemini(
    ocr_text: str,
    *,
    model_name: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: float = 2.0,
) -> GeminiExtractionResponse:
    """Send OCR text to Gemini and return structured extraction.

    Parameters
    ----------
    ocr_text:
        Raw OCR text from the medical report (as stored in ``medical_reports.ocr_text``).
    model_name:
        Gemini model to use.  Defaults to env ``GEMINI_MODEL`` or ``gemini-2.0-flash``.
    max_retries:
        Number of retry attempts on transient API errors.
    retry_delay:
        Base delay in seconds between retries (doubles each attempt).

    Returns
    -------
    GeminiExtractionResponse
        Validated extraction result with metadata and lab results.

    Raises
    ------
    ValueError
        If ``GEMINI_API_KEY`` is not set.
    RuntimeError
        If extraction fails after all retries.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set. "
            "Get a key from https://aistudio.google.com/app/apikey"
        )

    model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-3.1-pro-preview")
    client = genai.Client(api_key=api_key)
    _config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.1,  # Low temperature for deterministic extraction
        system_instruction=SYSTEM_PROMPT,
    )

    user_prompt = (
        "Extract ALL lab test results from the following OCR text of a medical report.\n"
        "Return ONLY the JSON object as specified in your instructions.\n\n"
        "═══════════════════════════════════════════════════\n"
        "OCR TEXT START\n"
        "═══════════════════════════════════════════════════\n\n"
        f"{ocr_text}\n\n"
        "═══════════════════════════════════════════════════\n"
        "OCR TEXT END\n"
        "═══════════════════════════════════════════════════"
    )

    last_error: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "Gemini extraction attempt %d/%d using model=%s (text length=%d chars)",
                attempt, max_retries, model_name, len(ocr_text),
            )

            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=_config,
            )
            raw_text = response.text

            if not raw_text or not raw_text.strip():
                raise RuntimeError("Gemini returned an empty response.")

            cleaned = _clean_json_response(raw_text)
            parsed = json.loads(cleaned)

            if isinstance(parsed, list):
                if len(parsed) == 1:
                    parsed = parsed[0]
                else:
                    raise ValueError(f"Expected a single JSON object, but got a list of {len(parsed)} items.")

            # Validate through Pydantic
            result = GeminiExtractionResponse.model_validate(parsed)

            logger.info(
                "Gemini extraction succeeded: %d lab results, metadata=%s",
                len(result.lab_results),
                result.metadata.model_dump(),
            )
            return result

        except json.JSONDecodeError as exc:
            last_error = exc
            logger.warning(
                "Gemini response was not valid JSON (attempt %d/%d): %s",
                attempt, max_retries, exc,
            )
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Gemini extraction failed (attempt %d/%d): %s",
                attempt, max_retries, exc,
            )

        if attempt < max_retries:
            sleep_time = retry_delay * (2 ** (attempt - 1))
            logger.info("Retrying in %.1f seconds…", sleep_time)
            time.sleep(sleep_time)

    raise RuntimeError(
        f"Gemini extraction failed after {max_retries} attempts. Last error: {last_error}"
    )


def extract_from_images_with_gemini(
    images: list,
    *,
    model_name: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: float = 2.0,
) -> GeminiExtractionResponse:
    """Send report page images directly to Gemini for vision-based extraction.

    Bypasses Tesseract OCR entirely — Gemini reads the images using its
    multimodal vision capabilities, extracting both structured lab results
    and the full text content in a single API call.

    Parameters
    ----------
    images:
        List of PIL.Image.Image objects (one per page of the report).
    model_name:
        Gemini model to use.  Defaults to env ``GEMINI_MODEL`` or ``gemini-2.0-flash``.
    max_retries:
        Number of retry attempts on transient API errors.
    retry_delay:
        Base delay in seconds between retries (doubles each attempt).

    Returns
    -------
    GeminiExtractionResponse
        Validated extraction result with metadata, lab results, and full_text.

    Raises
    ------
    ValueError
        If ``GEMINI_API_KEY`` is not set.
    RuntimeError
        If extraction fails after all retries.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set. "
            "Get a key from https://aistudio.google.com/app/apikey"
        )

    model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    client = genai.Client(api_key=api_key)

    # Extend the system prompt with full_text extraction instruction
    vision_system = (
        SYSTEM_PROMPT
        + "\n\n11. FULL TEXT EXTRACTION\n"
        "    • In addition to the structured lab results JSON, include a 'full_text'\n"
        "      field containing the COMPLETE text content you read from the report images.\n"
        "    • Preserve the original structure including line breaks.\n"
        "    • This text will be stored for future search and reference.\n"
    )

    _config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.1,
        system_instruction=vision_system,
    )

    user_prompt = (
        "These are pages from a medical lab report. "
        "Read the images directly and extract ALL lab test results.\n"
        "Return the JSON object as specified in your instructions.\n\n"
        "IMPORTANT: Include a 'full_text' field in your JSON response with the "
        "COMPLETE text you read from all pages, preserving structure and line breaks."
    )

    # Build multimodal content: page images + prompt
    contents: list = list(images)
    contents.append(user_prompt)

    last_error: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "Gemini vision extraction attempt %d/%d using model=%s (%d page images)",
                attempt, max_retries, model_name, len(images),
            )

            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=_config,
            )
            raw_text = response.text

            if not raw_text or not raw_text.strip():
                raise RuntimeError("Gemini returned an empty response.")

            cleaned = _clean_json_response(raw_text)
            parsed = json.loads(cleaned)

            if isinstance(parsed, list):
                if len(parsed) == 1:
                    parsed = parsed[0]
                else:
                    raise ValueError(f"Expected a single JSON object, but got a list of {len(parsed)} items.")

            # Validate through Pydantic
            result = GeminiExtractionResponse.model_validate(parsed)

            logger.info(
                "Gemini vision extraction succeeded: %d lab results, full_text_len=%d",
                len(result.lab_results),
                len(result.full_text) if result.full_text else 0,
            )
            return result

        except json.JSONDecodeError as exc:
            last_error = exc
            logger.warning(
                "Gemini response was not valid JSON (attempt %d/%d): %s",
                attempt, max_retries, exc,
            )
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Gemini vision extraction failed (attempt %d/%d): %s",
                attempt, max_retries, exc,
            )

        if attempt < max_retries:
            sleep_time = retry_delay * (2 ** (attempt - 1))
            logger.info("Retrying in %.1f seconds…", sleep_time)
            time.sleep(sleep_time)

    raise RuntimeError(
        f"Gemini vision extraction failed after {max_retries} attempts. Last error: {last_error}"
    )
