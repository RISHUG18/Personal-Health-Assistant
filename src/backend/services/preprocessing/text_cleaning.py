"""Core text-cleaning helpers for transforming noisy OCR output into structured lines."""

import re
from typing import List


MEASUREMENT_RE = re.compile(
    r"[A-Za-z][A-Za-z \(\)\/\-]+?\s+[0-9]+(?:\.[0-9]+)?\s*(?:mg/dL|g/dL|U/L|%|mmol|mEq|pg|nmol|thou|cells|fL|pg/mL|ng/mL|IU/L)?",
    re.IGNORECASE,
)


JUNK_PATTERNS = [
    r"Collected at",
    r"Processed at",
    r"National Reference laboratory",
    r"Test Report",
    r"Page\s*\d+",
    r"Dr\.",
    r"Authorized",
    r"IMPORTANT INSTRUCTIONS",
]


def break_into_lines(raw: str) -> List[str]:
    """Split a blob of OCR text into more line-like segments."""

    raw = raw.replace("  ", " ")
    raw = raw.replace("\t", " ")

    parts = re.split(r"(?=[A-Z][A-Za-z \(\)\/\-]{2,}\s+[0-9])", raw)

    lines: list[str] = []
    for part in parts:
        part = part.strip()
        if len(part) < 3:
            continue
        lines.append(part)
    return lines


def remove_junk(lines: List[str]) -> List[str]:
    """Remove repeated headers/metadata lines that do not carry medical signal."""

    cleaned: list[str] = []
    for line in lines:
        drop = False
        for pattern in JUNK_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                drop = True
                break
        if not drop:
            cleaned.append(line.strip())
    return cleaned


def clean_full_text(raw: str) -> str:
    """Run full cleaning pipeline and return newline-separated meaningful lines."""

    lines = break_into_lines(raw)
    lines = remove_junk(lines)

    final: list[str] = []
    for line in lines:
        if MEASUREMENT_RE.search(line) or len(line) > 25:
            final.append(line)

    return "\n".join(final)
