"""Deprecated shim.

Prefer importing from `services.retrieval.mock_retrieval`.
This module remains for backward compatibility with earlier imports.
"""

from services.retrieval.mock_retrieval import retrieve_mock_context  # noqa: F401

__all__ = ["retrieve_mock_context"]
