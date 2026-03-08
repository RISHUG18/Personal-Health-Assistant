"""Google Gemini API integration for structured lab data extraction.

Sends OCR text to Gemini with a carefully designed prompt that instructs the
model to extract every lab result, preserve exact numeric values, and return
structured JSON.  The response is validated into Pydantic models.

Uses the **new** ``google-genai`` SDK (``from google import genai``).

Environment variables
---------------------
GEMINI_API_KEY : str
    Google AI API key (required).  The ``genai.Client()`` reads this
    automatically from the environment.
GEMINI_MODEL : str
    Model name, defaults to ``gemini-3-flash-preview``.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Optional

from google import genai
<<<<<<< HEAD
=======
from google.genai import types
>>>>>>> 3529429295d941b8d284e08f90d46ba71835764d

from .models import (
    ExtractedLabResult,
    ExtractedReportMetadata,
    GeminiExtractionResponse,
)

logger = logging.getLogger(__name__)

# ── Prompt ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a COPY-PASTE extraction engine for medical laboratory reports.
Your ONLY function is to locate data that already exists in the OCR text
and transcribe it into JSON — nothing more.

You have NO authority to:
  ✗ Create values that are not in the source text
  ✗ Round, approximate, or alter any number
  ✗ Convert or normalize any unit
  ✗ Add medical interpretation, diagnosis, or commentary
  ✗ Compute derived values (e.g., do not calculate LDL if not printed)
  ✗ Fill in missing fields by inference

═══════════════════════════════════════════════════════════════════════════════
EXTRACTION RULES  (read every rule before outputting anything)
═══════════════════════════════════════════════════════════════════════════════

RULE 1 — COPY NUMBERS VERBATIM
  The source text is authoritative. Every digit, every decimal point, every
  leading zero must be copied character-for-character into "value_string".
  For "value" (the JSON number), reproduce the same precision:
    Source "13.52"  → value: 13.52,  value_string: "13.52"
    Source "0.03"   → value: 0.03,   value_string: "0.03"
    Source "120"    → value: 120,    value_string: "120"
  Do NOT round. Do NOT drop decimals. Do NOT add decimals that are not there.

RULE 2 — EXTRACT EVERY ROW
  Every row in the report that shows a test name + result must become one
  entry in lab_results. This includes:
    • All sub-tests in panels (Differential Count, Urine routine, LFT, etc.)
    • Calculated indices (MCV, MCH, MCHC, RDW, PDW, MPV, A/G ratio, etc.)
    • Any test where the result is a non-numeric word (Positive, Negative, etc.)
  Do NOT merge rows. Do NOT skip rows because they seem unimportant.

RULE 3 — NULL MEANS ABSENT, NOT UNCERTAIN
  Set a field to null only when the information is genuinely not present in
  the source text. Do NOT set null because you are unsure — if the text shows
  a value, copy it. If it is not there, null is correct.

RULE 4 — COPY UNITS VERBATIM
  Transcribe the unit exactly as it appears: character, case, symbols.
    "g/dL" → "g/dL"   (never "g/dl" or "G/DL")
    "10^3/uL" → "10^3/uL"   (never "10³/µL")
    "%" → "%"
  Do NOT translate, normalize, or simplify units.

RULE 5 — COPY REFERENCE RANGES VERBATIM
  Transcribe the full range string exactly as printed:
    "12.0 - 16.0", "< 200", "> 40", "4.5-5.5 x10^6/uL"
  Include any units that appear within the range string.
  If no range is printed for a test → null.

RULE 6 — ABNORMAL FLAG FROM EXPLICIT MARKERS ONLY
  Set is_abnormal = true  ONLY if the report explicitly marks the result:
    H, L, High, Low, *, ↑, ↓, A, Abnormal, or similar printed indicator.
  Set is_abnormal = false if the report explicitly marks it normal or in-range.
  Set is_abnormal = null  if no explicit marker is present.
  Do NOT compute abnormality from the reference range yourself.

RULE 7 — DATES: COPY THEN CONVERT FORMAT ONLY
  Find the report date in the text. Copy it, then reformat to YYYY-MM-DD.
  Prefer DD/MM/YYYY interpretation when the format is ambiguous.
  If no date is present → null.

RULE 8 — PAGE NUMBERS FROM MARKERS
  OCR text may contain "--- Page N ---" markers. Record which page each
  result was found on. If no markers → page_number: null for all rows.

RULE 9 — OCR NOISE: FIX NAMES ONLY, NEVER VALUES
  Tesseract OCR introduces artifacts (broken words, wrong characters).
  You MAY silently correct obvious misspellings in test_name only:
    "Hernoglobin" → "Hemoglobin"
    "Platelet Coont" → "Platelet Count"
  You MUST NOT touch any numeric value, unit, or reference range — even
  if they look wrong. They go into the output exactly as found.

RULE 10 — NON-NUMERIC RESULTS
  For results like Positive, Negative, Reactive, Present, Absent, Trace:
    value: null
    value_string: "<the word as printed>"
  The database value column is NUMERIC — null is the correct storage for
  these results. value_string preserves the original word.

═══════════════════════════════════════════════════════════════════════════════
OUTPUT FORMAT
Return ONLY a single valid JSON object. No markdown fences. No text before
or after the JSON. The structure must exactly match the schema below.
═══════════════════════════════════════════════════════════════════════════════

{
  "metadata": {
    "report_date": "YYYY-MM-DD or null",
    "report_type": "type of report as named in the document, or null",
    "patient_name": "patient name as printed, or null",
    "lab_name": "laboratory name as printed, or null"
  },
  "lab_results": [
    {
      "test_name": "full test name, OCR-corrected spelling only",
      "value": <number copied verbatim as JSON number, or null for non-numeric>,
      "value_string": "the exact string from the report (e.g. '13.52', 'Positive')",
      "unit": "unit exactly as printed, or null",
      "reference_range": "range exactly as printed, or null",
      "is_abnormal": <true if explicitly flagged | false if explicitly normal | null if no marker>,
      "page_number": <integer page number, or null>
    }
  ],
  "extraction_notes": "brief note on any genuinely illegible sections, or null"
}
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

    Uses the **new** ``google-genai`` SDK.  The client reads
    ``GEMINI_API_KEY`` from the environment automatically.

    Tries the configured model first, then falls back through a list of
    available models if the primary is overloaded (503) or quota-blocked (429).

    Parameters
    ----------
    ocr_text:
        Raw OCR text from the medical report (as stored in ``medical_reports.ocr_text``).
    model_name:
        Gemini model to use.  Defaults to env ``GEMINI_MODEL`` or ``gemini-2.5-flash``.
    max_retries:
        Number of retry attempts per model on transient errors.
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
        If extraction fails on all models after all retries.
    """
    if not os.getenv("GEMINI_API_KEY"):
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set. "
            "Get a key from https://aistudio.google.com/app/apikey"
        )

<<<<<<< HEAD
    primary = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Fallback chain: primary model first, then alternatives.
    # gemini-2.5-flash is the confirmed working primary.
    # gemini-3-flash-preview is a preview model — fast when available but often 503.
    # Older/lite variants serve as last-resort fallbacks.
    _FALLBACKS = [
        "gemini-2.5-flash",
        "gemini-3-flash-preview",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash-lite",
    ]
    model_chain = [primary] + [m for m in _FALLBACKS if m != primary]

    # Client reads GEMINI_API_KEY from environment automatically — same as apitest.py
    client = genai.Client()
=======
    model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    client = genai.Client(api_key=api_key)
    _config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.1,  # Low temperature for deterministic extraction
        system_instruction=SYSTEM_PROMPT,
    )
>>>>>>> 3529429295d941b8d284e08f90d46ba71835764d

    user_prompt = (
        SYSTEM_PROMPT + "\n\n"
        "TASK: Extract every lab test result from the OCR text below.\n"
        "CONSTRAINTS:\n"
        "  \u2022 Copy all values, units, and ranges character-for-character from the text.\n"
        "  \u2022 Do NOT add, remove, round, or reinterpret anything.\n"
        "  \u2022 Return ONLY a single JSON object \u2014 no markdown fences, no commentary.\n\n"
        "═══════════════════════════════════════════════════\n"
        "OCR TEXT START\n"
        "═══════════════════════════════════════════════════\n\n"
        f"{ocr_text}\n\n"
        "═══════════════════════════════════════════════════\n"
        "OCR TEXT END\n"
        "═══════════════════════════════════════════════════"
    )

    last_error: Optional[Exception] = None

    for current_model in model_chain:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    "Gemini extraction attempt %d/%d using model=%s (text length=%d chars)",
                    attempt, max_retries, current_model, len(ocr_text),
                )

<<<<<<< HEAD
                # Exact same call pattern as apitest.py — no config, no mime type.
                # JSON output is enforced entirely through the prompt.
                response = client.models.generate_content(
                    model=current_model,
                    contents=user_prompt,
                )
                raw_text = response.text
=======
            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=_config,
            )
            raw_text = response.text
>>>>>>> 3529429295d941b8d284e08f90d46ba71835764d

                if not raw_text or not raw_text.strip():
                    raise RuntimeError("Gemini returned an empty response.")

                cleaned = _clean_json_response(raw_text)
                parsed = json.loads(cleaned)

                # Validate through Pydantic
                result = GeminiExtractionResponse.model_validate(parsed)

                logger.info(
                    "Gemini extraction succeeded (model=%s): %d lab results, metadata=%s",
                    current_model, len(result.lab_results),
                    result.metadata.model_dump(),
                )
                return result

            except json.JSONDecodeError as exc:
                last_error = exc
                logger.warning(
                    "Gemini response was not valid JSON (model=%s, attempt %d/%d): %s",
                    current_model, attempt, max_retries, exc,
                )
            except Exception as exc:
                last_error = exc
                err_str = str(exc)
                logger.warning(
                    "Gemini extraction failed (model=%s, attempt %d/%d): %s",
                    current_model, attempt, max_retries, exc,
                )
                # 429 quota = quota-blocked; skip to next model immediately
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    logger.info(
                        "Model %s is quota-blocked (429), switching to next model.", current_model
                    )
                    break
                # 503 overloaded = preview model at capacity; skip after first failure
                if "503" in err_str or "overloaded" in err_str.lower() or "UNAVAILABLE" in err_str:
                    logger.info(
                        "Model %s is overloaded (503), switching to next model.", current_model
                    )
                    break

            if attempt < max_retries:
                sleep_time = retry_delay * (2 ** (attempt - 1))
                logger.info("Retrying in %.1f seconds…", sleep_time)
                time.sleep(sleep_time)

        logger.info("Model %s exhausted, trying next fallback…", current_model)

    raise RuntimeError(
        f"Gemini extraction failed on all models. Last error: {last_error}"
    )
