"""Normalization helpers for Gemini-extracted lab data.

Normalizes units to canonical forms and dates to ISO-8601, while preserving
the original values exactly as extracted.  Ambiguous fields are left as None.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

# ── Unit normalisation map ────────────────────────────────────────────────────
# Keys are lower-cased, whitespace-stripped variants; values are canonical forms.

_UNIT_MAP: dict[str, str] = {
    # Concentration — mass / volume
    "g/dl": "g/dL",
    "gm/dl": "g/dL",
    "g/l": "g/L",
    "mg/dl": "mg/dL",
    "mg/l": "mg/L",
    "ug/dl": "µg/dL",
    "µg/dl": "µg/dL",
    "ug/l": "µg/L",
    "µg/l": "µg/L",
    "ng/ml": "ng/mL",
    "ng/dl": "ng/dL",
    "pg/ml": "pg/mL",
    "pg/dl": "pg/dL",
    # Concentration — molar
    "mmol/l": "mmol/L",
    "umol/l": "µmol/L",
    "µmol/l": "µmol/L",
    "nmol/l": "nmol/L",
    # Enzyme activity
    "iu/l": "IU/L",
    "u/l": "U/L",
    "iu/ml": "IU/mL",
    "miu/ml": "mIU/mL",
    "uiu/ml": "µIU/mL",
    "µiu/ml": "µIU/mL",
    # Electrolytes
    "meq/l": "mEq/L",
    "meq/dl": "mEq/dL",
    # Cell counts
    "/ul": "/µL",
    "/µl": "/µL",
    "cells/ul": "cells/µL",
    "cells/µl": "cells/µL",
    "10^3/ul": "10³/µL",
    "10^3/µl": "10³/µL",
    "x10^3/ul": "10³/µL",
    "x10^3/µl": "10³/µL",
    "thou/ul": "10³/µL",
    "k/ul": "10³/µL",
    "10^6/ul": "10⁶/µL",
    "10^6/µl": "10⁶/µL",
    "x10^6/ul": "10⁶/µL",
    "x10^6/µl": "10⁶/µL",
    "mil/ul": "10⁶/µL",
    "m/ul": "10⁶/µL",
    "10^9/l": "10⁹/L",
    "x10^9/l": "10⁹/L",
    # Hematology
    "fl": "fL",
    "pg": "pg",
    # Percentage
    "%": "%",
    # Sedimentation / time
    "mm/hr": "mm/hr",
    "mm/h": "mm/hr",
    "sec": "sec",
    "seconds": "sec",
    "mins": "min",
    "minutes": "min",
    # Urine
    "mg/24hr": "mg/24hr",
    "mg/24h": "mg/24hr",
    "ml/min": "mL/min",
    "ml/min/1.73m2": "mL/min/1.73m²",
    # Coagulation
    "inr": "INR",
    # Misc
    "copies/ml": "copies/mL",
    "ratio": "ratio",
}


def normalize_unit(raw_unit: Optional[str]) -> Optional[str]:
    """Normalize a measurement unit to its canonical form.

    Returns the canonical unit string, the original string if no mapping exists,
    or None if the input is empty/None.
    """
    if not raw_unit:
        return None
    cleaned = raw_unit.strip()
    if not cleaned:
        return None
    key = cleaned.lower().replace(" ", "")
    # Return mapped value or original (Gemini usually gets the casing right)
    return _UNIT_MAP.get(key, cleaned)


# ── Date normalisation ────────────────────────────────────────────────────────

_DATE_FORMATS = (
    "%Y-%m-%d",       # 2024-03-15
    "%Y/%m/%d",       # 2024/03/15
    "%d-%m-%Y",       # 15-03-2024
    "%d/%m/%Y",       # 15/03/2024
    "%d-%b-%Y",       # 15-Mar-2024
    "%d %b %Y",       # 15 Mar 2024
    "%d %B %Y",       # 15 March 2024
    "%b %d, %Y",      # Mar 15, 2024
    "%B %d, %Y",      # March 15, 2024
    "%m-%d-%Y",       # 03-15-2024
    "%m/%d/%Y",       # 03/15/2024
    "%d.%m.%Y",       # 15.03.2024
    "%Y.%m.%d",       # 2024.03.15
)


def normalize_date(raw_date: Optional[str]) -> Optional[str]:
    """Normalize a date string to ISO-8601 ``YYYY-MM-DD`` format.

    Tries multiple common formats.  Returns None if parsing fails
    (ambiguous dates are left as None rather than guessed).
    """
    if not raw_date:
        return None
    candidate = raw_date.strip()
    if not candidate:
        return None

    # If already in ISO format, return as-is
    if re.match(r"^\d{4}-\d{2}-\d{2}$", candidate):
        return candidate

    for fmt in _DATE_FORMATS:
        try:
            parsed = datetime.strptime(candidate, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def normalize_test_name(raw_name: str) -> str:
    """Clean up a test name: trim whitespace, normalize spacing."""
    if not raw_name:
        return raw_name
    # Collapse multiple spaces
    cleaned = re.sub(r"\s+", " ", raw_name.strip())
    return cleaned


def normalize_reference_range(raw_range: Optional[str]) -> Optional[str]:
    """Trim reference range string. Returns None if empty."""
    if not raw_range:
        return None
    cleaned = raw_range.strip()
    return cleaned or None


def parse_numeric_range(raw_range: Optional[str]) -> tuple[Optional[float], Optional[float]]:
    """Parse a reference range like '12-16' or '12.0 – 16.0' into (low, high).

    Returns (None, None) if the range cannot be parsed.
    """
    if not raw_range:
        return None, None
    match = re.search(
        r"(?P<low>\d+(?:\.\d+)?)\s*[-–—]\s*(?P<high>\d+(?:\.\d+)?)", raw_range
    )
    if not match:
        return None, None
    try:
        low = float(match.group("low"))
        high = float(match.group("high"))
        return low, high
    except (TypeError, ValueError):
        return None, None
