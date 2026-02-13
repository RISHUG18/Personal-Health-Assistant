"""Deprecated shim.

Prefer importing from `services.preprocessing.chunking`.
This module remains for backward compatibility with earlier imports.
"""

from backend.services.preprocessing.chunking import (  # noqa: F401
    HEADING_RE,
    MEASUREMENT_RE,
    doc_to_chunks,
    extract_table_rows,
    recursive_split,
    split_into_sections,
)

# NOTE: This shim intentionally keeps the legacy import surface (`services.*`).
# Prefer using `backend.services.preprocessing.chunking` in new code.

__all__ = [
    "HEADING_RE",
    "MEASUREMENT_RE",
    "split_into_sections",
    "extract_table_rows",
    "recursive_split",
    "doc_to_chunks",
]
