"""Core text-cleaning helpers for transforming noisy OCR output into structured lines."""

import re
from typing import List


MEASUREMENT_RE = re.compile(
    r"[A-Za-z][A-Za-z0-9 \(\)\/\-]+?\s+[0-9]+(?:\.[0-9]+)?\s*(?:mg/dL|g/dL|U/L|%|mmol|mEq|pg|nmol|thou|cells|fL|pg/mL|ng/mL|IU/L)?",
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
    """Split a blob of OCR text into more line-like segments.

    Strategy:
    1. Split on actual newlines first (OCR usually preserves them).
    2. For any remaining long line that looks like concatenated measurements,
       apply a regex split to pull them apart — but only when the line is
       clearly multi-measurement (> 60 chars).
    """
    raw = raw.replace("  ", " ")
    raw = raw.replace("\t", " ")

    # Primary split: honour existing line breaks
    raw_lines = raw.splitlines()

    _CONCAT_RE = re.compile(r"(?=[A-Z][A-Za-z0-9 \(\)\/\-]{2,}\s+[0-9])")

    lines: list[str] = []
    for raw_line in raw_lines:
        raw_line = raw_line.strip()
        if len(raw_line) < 3:
            continue
        # Only regex-split long lines that likely contain multiple measurements
        if len(raw_line) > 60:
            parts = _CONCAT_RE.split(raw_line)
            for part in parts:
                part = part.strip()
                if len(part) >= 3:
                    lines.append(part)
        else:
            lines.append(raw_line)
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
