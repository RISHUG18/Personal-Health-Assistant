"""Deprecated shim.

Prefer importing from `services.preprocessing.text_cleaning`.
This module remains for backward compatibility with earlier imports.
"""

from services.preprocessing.text_cleaning import (  # noqa: F401
    JUNK_PATTERNS,
    MEASUREMENT_RE,
    break_into_lines,
    clean_full_text,
    remove_junk,
)

__all__ = [
    "MEASUREMENT_RE",
    "JUNK_PATTERNS",
    "break_into_lines",
    "remove_junk",
    "clean_full_text",
]
