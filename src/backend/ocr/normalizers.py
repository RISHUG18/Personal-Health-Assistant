"""Normalization helpers for deterministic OCR extraction."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

_UNIT_ALIASES = {
    "g/dl": "g/dL",
    "gdL": "g/dL",
    "g/dL": "g/dL",
    "mg/dl": "mg/dL",
    "mg/dL": "mg/dL",
    "mmol/l": "mmol/L",
    "mmol/L": "mmol/L",
    "umol/l": "umol/L",
    "umol/L": "umol/L",
    "µmol/l": "µmol/L",
    "µmol/L": "µmol/L",
    "iu/l": "IU/L",
    "IU/L": "IU/L",
    "u/l": "U/L",
    "U/L": "U/L",
    "%": "%",
    "/ul": "/µL",
    "/µl": "/µL",
    "/µL": "/µL",
    "10^3/ul": "10^3/µL",
    "10^3/µl": "10^3/µL",
    "10^3/µl": "10^3/µL",
    "10^3/µL": "10^3/µL",
    "x10^3/ul": "10^3/µL",
    "x10^3/µl": "10^3/µL",
    "x10^3/µL": "10^3/µL",
    "10^9/l": "10^9/L",
    "10^9/L": "10^9/L",
    "x10^9/l": "10^9/L",
    "x10^9/L": "10^9/L",
}


def normalize_unit(raw_unit: str) -> Optional[str]:
    """Normalize unit spelling/case only. Returns None if unknown."""
    if not raw_unit:
        return None
    cleaned = raw_unit.strip()
    lowered = cleaned.lower().replace(" ", "")
    return _UNIT_ALIASES.get(lowered)


def normalize_numeric(raw_value: str) -> Optional[float]:
    """Convert numeric strings to float. Returns None on failure."""
    if not raw_value:
        return None
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return None


def normalize_reference_range(raw_range: str) -> Optional[str]:
    """Keep reference range as raw text, trimmed. Returns None if empty."""
    if not raw_range:
        return None
    cleaned = raw_range.strip()
    return cleaned or None


_DATE_PATTERNS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%m-%d-%Y",
    "%m/%d/%Y",
)


def normalize_date(raw_date: str) -> Optional[str]:
    """Normalize date to YYYY-MM-DD. Returns None if parsing fails."""
    if not raw_date:
        return None
    candidate = raw_date.strip()
    for fmt in _DATE_PATTERNS:
        try:
            parsed = datetime.strptime(candidate, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_numeric_range(raw_range: str) -> tuple[Optional[float], Optional[float]]:
    """Parse reference range like '12-16' or '12–16'. Returns (low, high)."""
    if not raw_range:
        return None, None
    match = re.search(r"(?P<low>\d+(?:\.\d+)?)\s*[-–]\s*(?P<high>\d+(?:\.\d+)?)", raw_range)
    if not match:
        return None, None
    low = normalize_numeric(match.group("low"))
    high = normalize_numeric(match.group("high"))
    return low, high
