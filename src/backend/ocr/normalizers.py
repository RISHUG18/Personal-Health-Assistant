"""Normalization helpers for deterministic (regex-based) OCR extraction.

These functions are intentionally minimal — they serve the regex pipeline
only (ocr/extractors.py → ocr/inserters.py).  For the Gemini AI pipeline,
see extraction/normalizer.py which has a much broader unit map and handles
OCR noise such as µ/y confusion and trailing punctuation.
"""
from __future__ import annotations

import re
from typing import Optional

# ── Unit aliases ─────────────────────────────────────────────────────────────
# Maps lower-cased, whitespace-stripped variants to the canonical form.
# Returns None for unknown units — regex extractor will skip those results.

_UNIT_ALIASES: dict[str, str] = {
    "g/dl":       "g/dL",
    "gm/dl":      "g/dL",
    "mg/dl":      "mg/dL",
    "mmol/l":     "mmol/L",
    "umol/l":     "µmol/L",
    "µmol/l":     "µmol/L",
    "nmol/l":     "nmol/L",
    "iu/l":       "IU/L",
    "u/l":        "U/L",
    "%":          "%",
    "/ul":        "/µL",
    "/µl":        "/µL",
    "10^3/ul":    "10³/µL",
    "10^3/µl":    "10³/µL",
    "x10^3/ul":   "10³/µL",
    "x10^3/µl":   "10³/µL",
    "10^6/ul":    "10⁶/µL",
    "10^6/µl":    "10⁶/µL",
    "x10^6/ul":   "10⁶/µL",
    "x10^6/µl":   "10⁶/µL",
    "10^9/l":     "10⁹/L",
    "x10^9/l":    "10⁹/L",
    "fl":         "fL",
    "pg":         "pg",
    "ng/ml":      "ng/mL",
    "ng/dl":      "ng/dL",
    "pg/ml":      "pg/mL",
    "ug/dl":      "µg/dL",
    "µg/dl":      "µg/dL",
    "miu/ml":     "mIU/mL",
    "µiu/ml":     "µIU/mL",
    "mm/hr":      "mm/hr",
    "mm/h":       "mm/hr",
    "mg/24hr":    "mg/24hr",
    "ml/min":     "mL/min",
    "inr":        "INR",
    "meq/l":      "mEq/L",
}


def normalize_unit(raw_unit: str) -> Optional[str]:
    """Normalize unit to canonical form.

    Returns ``None`` for unrecognised units — the regex extractor treats
    ``None`` as a skip signal, keeping extraction conservative.
    """
    if not raw_unit:
        return None
    key = raw_unit.strip().lower().replace(" ", "")
    return _UNIT_ALIASES.get(key)  # None = unknown → extractor skips row


def normalize_numeric(raw_value: str) -> Optional[float]:
    """Parse a numeric string to float. Returns None on failure."""
    if not raw_value:
        return None
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return None


def normalize_reference_range(raw_range: str) -> Optional[str]:
    """Trim reference range string. Returns None if empty."""
    if not raw_range:
        return None
    cleaned = raw_range.strip()
    return cleaned or None


def parse_numeric_range(raw_range: str) -> tuple[Optional[float], Optional[float]]:
    """Parse a reference range like '12-16' or '12.0–16.0' into (low, high).

    Returns (None, None) if the range cannot be parsed.
    """
    if not raw_range:
        return None, None
    match = re.search(
        r"(?P<low>\d+(?:\.\d+)?)\s*[-–—]\s*(?P<high>\d+(?:\.\d+)?)", raw_range
    )
    if not match:
        return None, None
    low  = normalize_numeric(match.group("low"))
    high = normalize_numeric(match.group("high"))
    return low, high
