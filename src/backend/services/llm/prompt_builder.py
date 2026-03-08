"""Prompt builder — Single Responsibility: construct the exact prompt string
that will be sent to the LLM, and nothing else.

Prompt structure (fixed)
------------------------
::

    <system_instruction>
    ... role-specific rules ...
    </system_instruction>

    MEDICAL CONTEXT DATA:
    ```json
    { ... BuiltContext dict ... }
    ```

    USER QUERY:
    <query>

This strict structure separates the instruction space from the data space and
from the user turn, which reduces prompt-injection risk and helps the model
reliably parse the JSON context block.
"""
from __future__ import annotations

import json
import logging
import os
from functools import lru_cache # for caching loaded prompts
from pathlib import Path

logger = logging.getLogger(__name__)

# Resolved once at import time — prompts/ sits two levels above this file:
# services/llm/  →  services/  →  backend/  →  prompts/
_PROMPTS_DIR: Path = Path(__file__).resolve().parent.parent.parent / "prompts"

# Mapping from the role string (matching ``BuiltContext.role``) to its file.
_PROMPT_FILES: dict[str, str] = {
    "user": "system_user.txt",
    "doctor": "system_doctor.txt",
}


@lru_cache(maxsize=4)
def load_system_prompt(role: str) -> str:
    """Load and cache the system prompt for the given role.

    Cached with :func:`functools.lru_cache` so disk reads happen only once per
    process per unique role string.

    Parameters
    ----------
    role:
        Either ``"user"`` (wellbeing coach) or ``"doctor"`` (clinical
        assistant).  Any unknown role falls back to the ``"user"`` prompt with
        a warning so the pipeline continues without crashing.

    Returns
    -------
    str
        Full system-prompt text.

    Raises
    ------
    FileNotFoundError
        If the expected prompt file is missing from ``prompts/``.
    """
    filename = _PROMPT_FILES.get(role)
    if filename is None:
        logger.warning(
            "Unknown role '%s'; falling back to 'user' system prompt.", role
        )
        filename = _PROMPT_FILES["user"]

    prompt_path = _PROMPTS_DIR / filename
    if not prompt_path.exists():
        raise FileNotFoundError(
            f"System prompt file not found: {prompt_path}. "
            "Ensure prompts/system_user.txt and prompts/system_doctor.txt exist."
        )

    text = prompt_path.read_text(encoding="utf-8").strip()
    logger.debug("Loaded system prompt for role='%s' (%d chars).", role, len(text))
    return text


def build_prompt(query: str, context_dict: dict) -> str:
    """Serialise the assembled context into the formatted user-turn string.

    This function produces only the *user turn* of the prompt — the part that
    changes per request.  The system instruction is handled separately by
    :func:`load_system_prompt` so the two concerns stay independent.

    The context is represented as an indented JSON block because Gemini (and
    most LLMs) reliably parses structured JSON keys such as
    ``"active_alerts"`` and ``"retrieved_chunks"`` better than free-form text.

    Parameters
    ----------
    query:
        The original user question to be placed at the bottom of the prompt,
        clearly separated from the context block.
    context_dict:
        The serialisable ``BuiltContext`` payload (result of
        ``.model_dump()``).

    Returns
    -------
    str
        The formatted prompt string ready to be passed as the ``contents``
        argument to an LLM client.

    Notes
    -----
    * ``indent=2`` produces readable JSON that helps the model parse nested
      keys while keeping token usage reasonable.
    * The ``USER QUERY:`` label is on its own line so a prompt-injection
      attempt embedded in the JSON context cannot impersonate the query.
    """
    context_str = json.dumps(context_dict, indent=2, default=str)
    return (
        "MEDICAL CONTEXT DATA:\n"
        "```json\n"
        f"{context_str}\n"
        "```\n\n"
        f"USER QUERY:\n{query}"
    )
