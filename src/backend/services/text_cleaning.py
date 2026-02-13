"""Deprecated shim.

Prefer importing from `services.preprocessing.text_cleaning`.
This module remains for backward compatibility with earlier imports.
"""

from backend.services.preprocessing.text_cleaning import (  # noqa: F401
    JUNK_PATTERNS,
    MEASUREMENT_RE,
    break_into_lines,
    clean_full_text,
    remove_junk,
)

# NOTE: This shim intentionally keeps the legacy import surface (`services.*`).
# Prefer using `backend.services.preprocessing.text_cleaning` in new code.

__all__ = [
    "MEASUREMENT_RE",
    "JUNK_PATTERNS",
    "break_into_lines",
    "remove_junk",
    "clean_full_text",
]
