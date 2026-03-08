"""LLM service package — public API.

Exports
-------
GeminiService
    Concrete Gemini implementation of :class:`LLMProvider`.
LLMProvider
    Protocol that any LLM back-end must satisfy (use for type hints).
load_system_prompt
    Load and cache a role-specific **behavioural** system prompt from ``prompts/``.
load_citation_instructions
    Load and cache role-specific **citation** instructions from ``prompts/``.
build_prompt
    Assemble a ``BuiltContext`` dict into the formatted user-turn prompt
    (context JSON + conditional citation block + user query).

Prompt files in ``prompts/``
-----------------------------
::

    prompts/
        system_user.txt       — behavioural rules for the wellbeing coach
        system_doctor.txt     — behavioural rules for the clinical assistant
        citation_user.txt     — grounding / citation rules for the user role
        citation_doctor.txt   — grounding / citation rules for the doctor role

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
from backend.services.llm.prompt_builder import (
    build_prompt,
    load_citation_instructions,
    load_system_prompt,
)

__all__ = [
    "GeminiService",
    "LLMProvider",
    "build_prompt",
    "load_citation_instructions",
    "load_system_prompt",
]
