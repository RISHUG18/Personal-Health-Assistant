"""LLM service package — public API.

Exports
-------
GeminiService
    Concrete Gemini implementation of :class:`LLMProvider`.
LLMProvider
    Protocol that any LLM back-end must satisfy (use for type hints).
load_system_prompt
    Load and cache a role-specific system prompt from ``prompts/``.
build_prompt
    Serialise a ``BuiltContext`` dict into the formatted user-turn prompt.

Typical usage
-------------
::

    from backend.services.llm import GeminiService, load_system_prompt

    llm = GeminiService()                            # reads GEMINI_API_KEY
    system_prompt = load_system_prompt(role="user")
    answer = llm.generate(
        query=body.query,
        context_dict=context.model_dump(),
        system_instruction=system_prompt,
    )
"""

from backend.services.llm.gemini_service import GeminiService
from backend.services.llm.interfaces import LLMProvider
from backend.services.llm.prompt_builder import build_prompt, load_system_prompt

__all__ = [
    "GeminiService",
    "LLMProvider",
    "build_prompt",
    "load_system_prompt",
]
