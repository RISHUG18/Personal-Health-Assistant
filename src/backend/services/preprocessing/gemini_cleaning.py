"""LLM-based semantic cleaning of OCR medical-report text using Google Gemini.

This module sits between the deterministic regex cleaning stage
(:func:`~backend.services.preprocessing.text_cleaning.clean_full_text`) and
the chunking stage (:func:`~backend.services.preprocessing.chunking.doc_to_chunks_with_metadata`)
in the RAG ingestion pipeline.

Usage::

    from backend.services.preprocessing.gemini_cleaning import gemini_clean_report

    llm_cleaned = gemini_clean_report(regex_cleaned_text)

The function is intentionally **best-effort**: if the Gemini call fails for
any reason (missing API key, quota exceeded, network error) the function
returns the *original* text unchanged and logs a warning, so that the rest
of the pipeline can continue with the regex-only output.
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Optional

logger = logging.getLogger(__name__)

# ── Prompt ────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a medical-report text cleaner.  Your ONLY job is to remove noise
from OCR-scanned medical lab reports and reorganise the remaining medically
relevant content into clear sections.

═══════════════════════════════════════════════════════════════════════════════
WHAT TO REMOVE
═══════════════════════════════════════════════════════════════════════════════
• Postal/street addresses, city names, PIN codes, and geographical details.
• Phone numbers, fax numbers, email addresses, and website URLs.
• Lab accreditation/registration statements (NABL, ISO, CAP, etc.).
• Barcodes, QR-code placeholders, page numbers, report IDs/serial numbers.
• Signatures, "Authorized Signatory", and stamp text.
• Marketing slogans, disclaimers, and legal boilerplate.
• Repeated header/footer lines that appear on every page.
• Collection/processing timestamps that carry no clinical value.

═══════════════════════════════════════════════════════════════════════════════
WHAT TO KEEP
═══════════════════════════════════════════════════════════════════════════════
• Patient name, age, sex, patient/sample ID.
• All test names, measured values, units, and reference ranges.
• Abnormal-flag markers (H, L, *, ↑, ↓, out-of-range notes).
• Clinical interpretation notes, physician comments, and specialist summaries.
• Report date (sample collection / reporting date).

═══════════════════════════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════════════════════════
Reorganise the kept text into these sections (omit a section if it has no
relevant content):

    ## Patient Information
    ## Blood Test Results
    ## Biochemistry Results
    ## Hormones & Vitamins
    ## Urinalysis
    ## Interpretation Notes

Within each section, present test results clearly — one test per line
where possible, preserving the original values, units, and ranges.

═══════════════════════════════════════════════════════════════════════════════
CRITICAL CONSTRAINTS
═══════════════════════════════════════════════════════════════════════════════
1. Do NOT add new information or interpretations.
   Only reorganize and clean the text that already exists.
2. Do NOT invent test results, values, or medical terms not in the input.
3. Do NOT change any numeric values or units — keep them verbatim.
4. Correct obvious OCR misspellings in test names only
   (e.g., "Hernoglobin" → "Hemoglobin").
5. Output plain text (Markdown headers are fine), NOT JSON.
"""


def gemini_clean_report(
    text: str,
    *,
    model_name: Optional[str] = None,
    max_retries: int = 2,
    retry_delay: float = 2.0,
) -> str:
    """Semantically clean a regex-cleaned medical report using Gemini.

    Parameters
    ----------
    text:
        The report text *after* deterministic regex cleaning.
    model_name:
        Gemini model to use (default: env ``GEMINI_MODEL`` or
        ``gemini-2.0-flash``).
    max_retries:
        Retry count on transient API errors.
    retry_delay:
        Base back-off delay in seconds (doubled each attempt).

    Returns
    -------
    str
        The LLM-cleaned text, or the *original* ``text`` if the call fails.
    """
    # ── Guard: API key ────────────────────────────────────────────────────────
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning(
            "[gemini_clean] GEMINI_API_KEY not set — skipping semantic cleaning."
        )
        return text

    # Lazy import so the module can be loaded without google-genai installed
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        logger.warning(
            "[gemini_clean] google-genai not installed — skipping semantic cleaning."
        )
        return text

    model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        temperature=0.1,
        system_instruction=_SYSTEM_PROMPT,
    )

    user_prompt = (
        "Clean and reorganise the following OCR text of a medical lab report.\n"
        "Remove all non-medical noise and reorganise the medically relevant "
        "content into clear sections as described in your instructions.\n\n"
        "═══════════════════════════════════════════════════\n"
        "OCR TEXT START\n"
        "═══════════════════════════════════════════════════\n\n"
        f"{text}\n\n"
        "═══════════════════════════════════════════════════\n"
        "OCR TEXT END\n"
        "═══════════════════════════════════════════════════"
    )

    last_error: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "[gemini_clean] attempt %d/%d  model=%s  input_len=%d",
                attempt, max_retries, model_name, len(text),
            )
            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=config,
            )
            result = (response.text or "").strip()

            if not result:
                raise RuntimeError("Gemini returned empty response.")

            # Strip markdown code fences if present
            if result.startswith("```"):
                result = re.sub(r"^```(?:\w+)?\s*", "", result)
                result = re.sub(r"\s*```$", "", result)

            logger.info(
                "[gemini_clean] SUCCESS — output_len=%d (input_len=%d, reduction=%.0f%%)",
                len(result), len(text),
                (1 - len(result) / len(text)) * 100 if text else 0,
            )
            return result

        except Exception as exc:
            last_error = exc
            logger.warning(
                "[gemini_clean] attempt %d/%d FAILED: %s",
                attempt, max_retries, exc,
            )
            if attempt < max_retries:
                sleep_time = retry_delay * (2 ** (attempt - 1))
                logger.info("[gemini_clean] retrying in %.1fs…", sleep_time)
                time.sleep(sleep_time)

    # All retries exhausted — fall back to the input unchanged.
    logger.error(
        "[gemini_clean] All %d attempts failed (last error: %s). "
        "Falling back to regex-only cleaned text.",
        max_retries, last_error,
    )
    return text
