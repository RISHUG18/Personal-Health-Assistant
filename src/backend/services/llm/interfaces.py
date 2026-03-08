"""LLM provider interface — the Dependency Inversion anchor for the LLM layer.

Any concrete LLM back-end (Gemini, OpenAI, local Ollama, …) must satisfy this
protocol.  The route and any other caller depend *only* on this interface, not
on a concrete implementation, keeping the system Open/Closed.

Usage
-----
::

    from backend.services.llm.interfaces import LLMProvider

    def generate_answer(provider: LLMProvider, query: str, ctx: dict) -> str:
        return provider.generate(query=query, context_dict=ctx)
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Abstract contract that every LLM back-end must implement.

    ``@runtime_checkable`` lets callers use ``isinstance(obj, LLMProvider)``
    for defensive checks without requiring inheritance.
    """

    def generate(
        self,
        *,
        query: str,
        context_dict: dict,
        system_instruction: str,
    ) -> str:
        """Generate a grounded natural-language response.

        Parameters
        ----------
        query:
            The original user question, verbatim.
        context_dict:
            The serialisable payload produced by
            :func:`~backend.services.context.context_builder.build_context`
            (``.model_dump()``).
        system_instruction:
            The full system-prompt string (role-specific rules loaded from
            ``prompts/system_user.txt`` or ``prompts/system_doctor.txt``).

        Returns
        -------
        str
            Markdown-formatted response text.

        Raises
        ------
        RuntimeError
            On configuration errors (missing API key, bad model name, …) or
            network / API failures.
        """
        ...
