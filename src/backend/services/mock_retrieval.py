"""Deprecated shim.

Prefer importing from `services.retrieval.mock_retrieval`.
This module remains for backward compatibility with earlier imports.
"""

from backend.services.retrieval.mock_retrieval import retrieve_mock_context  # noqa: F401

# NOTE: This shim intentionally keeps the legacy import surface (`services.*`).
# Prefer using `backend.services.retrieval.mock_retrieval` in new code.

__all__ = ["retrieve_mock_context"]
