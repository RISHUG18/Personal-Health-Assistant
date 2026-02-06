"""Regex-only extraction for lab results from OCR text."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Optional

from .normalizers import normalize_numeric, normalize_reference_range, normalize_unit


@dataclass(frozen=True)
class LabExtraction:
    test_name: str
    value: float
    unit: str
    reference_range: Optional[str]
    extracted_from_page: Optional[int]


# Explicit, allow-listed lab test names (no inference).
_TEST_NAMES = [
    "Hemoglobin",
    "Hgb",
    "Hb",
    "WBC",
    "Platelets",
    "PLT",
    "RBC",
    "Hematocrit",
    "HCT",
    "MCV",
    "MCH",
    "MCHC",
    "RDW",
    "Neutrophils",
    "Lymphocytes",
    "Monocytes",
    "Eosinophils",
    "Basophils",
    "Glucose",
    "Glucose Fasting",
    "Creatinine",
    "Urea",
    "BUN",
    "Sodium",
    "Potassium",
    "Chloride",
    "Calcium",
    "Magnesium",
    "Phosphorus",
    "Albumin",
    "Total Protein",
    "AST",
    "ALT",
    "ALP",
    "Bilirubin",
    "Triglycerides",
    "HDL",
    "LDL",
    "Total Cholesterol",
]

_TEST_NAMES_REGEX = r"(?:" + "|".join(re.escape(name) for name in _TEST_NAMES) + r")"

# Fully anchored pattern to avoid partial matches.
# Example line: "Hemoglobin: 9.8 g/dL (Normal: 12–16)"
_LINE_PATTERN = re.compile(
    rf"^\s*(?P<test>{_TEST_NAMES_REGEX})\s*[:\-]?\s*"
    r"(?P<value>\d+(?:\.\d+)?)\s*"
    r"(?P<unit>[A-Za-z%/µµ0-9^\.\-]+)"
    r"(?:\s*(?:\((?:Normal|Ref(?:erence)?|Range)[:\s]*"\
    r"(?P<range>[^\)]+)\)|(?:Ref(?:erence)?\s*Range[:\s]*"\
    r"(?P<range2>[\d\.\s\-–<>]+))))?\s*$",
    re.IGNORECASE,
)

_INLINE_PATTERN = re.compile(
    rf"\b(?P<test>{_TEST_NAMES_REGEX})\b\s*[:\-]?\s*"
    r"(?P<value>\d+(?:\.\d+)?)\s*"
    r"(?P<unit>[A-Za-z%/µµ0-9^\.\-]+)"
    r"(?:\s*\((?:Normal|Ref(?:erence)?|Range)[:\s]*"
    r"(?P<range>[^\)]+)\))?",
    re.IGNORECASE,
)

_PAGE_PATTERN = re.compile(r"^\s*Page\s+(?P<page>\d+)\s*$", re.IGNORECASE)


def extract_lab_results(ocr_text: str) -> List[LabExtraction]:
    """Extract lab results from OCR text using regex-only rules."""
    results: List[LabExtraction] = []
    current_page: Optional[int] = None

    for raw_line in ocr_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        page_match = _PAGE_PATTERN.match(line)
        if page_match:
            try:
                current_page = int(page_match.group("page"))
            except ValueError:
                current_page = None
            continue

        match = _LINE_PATTERN.match(line)
        if not match:
            continue

        test_name = match.group("test")
        value = normalize_numeric(match.group("value"))
        unit = normalize_unit(match.group("unit"))
        reference_range = normalize_reference_range(
            match.group("range") or match.group("range2") or ""
        )

        if value is None or unit is None:
            # Skip if required fields are not confidently parsed.
            continue

        results.append(
            LabExtraction(
                test_name=test_name,
                value=value,
                unit=unit,
                reference_range=reference_range,
                extracted_from_page=current_page,
            )
        )

    if results:
        return results

    # Fallback: scan inline if OCR collapsed line breaks.
    for match in _INLINE_PATTERN.finditer(ocr_text):
        test_name = match.group("test")
        value = normalize_numeric(match.group("value"))
        unit = normalize_unit(match.group("unit"))
        reference_range = normalize_reference_range(match.group("range") or "")

        if value is None or unit is None:
            continue

        results.append(
            LabExtraction(
                test_name=test_name,
                value=value,
                unit=unit,
                reference_range=reference_range,
                extracted_from_page=None,
            )
        )

    return results
