"""Context builder services — assembles all retrieved data into a structured
object ready for the LLM (Gemini).

Single Responsibility: this package ONLY assembles. It never:
- fetches from the database (see data_fetchers.py)
- embeds queries  (see services/embeddings/)
- calls Gemini    (future services/llm/)

Public API
----------
``build_context``
    Core assembly function.  Returns a validated :class:`BuiltContext`.
``BuiltContext``
    Pydantic model that represents the complete context object.
"""

from backend.services.context.context_builder import (
    BuiltContext,
    build_context,
)

__all__ = ["build_context", "BuiltContext"]
