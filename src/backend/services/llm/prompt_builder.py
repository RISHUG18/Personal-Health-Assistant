"""Prompt builder — Single Responsibility: construct the exact prompt string
that will be sent to the LLM, and nothing else.

All human-readable text lives in files under ``prompts/``.  Python code owns
only the *structure* (what goes where) and the *conditional logic* (whether a
block is included).  This separation means wording changes never require a
code deploy — just edit the text file.

File layout in ``prompts/``
---------------------------
::

    prompts/
        system_user.txt       — behavioural rules for the wellbeing-coach role
        system_doctor.txt     — behavioural rules for the clinical-assistant role
        citation_user.txt     — grounding / citation rules for the user role
        citation_doctor.txt   — grounding / citation rules for the doctor role

Adding a new role
-----------------
1. Create ``prompts/system_<role>.txt`` and ``prompts/citation_<role>.txt``.
2. Add the role name as a key to ``_PROMPT_FILES`` and ``_CITATION_FILES``.
3. No other code changes are needed (Open/Closed Principle).

Prompt structure (user-turn)
----------------------------
::

    MEDICAL CONTEXT DATA:
    ```json
    { ... BuiltContext dict ... }
    ```

    --- CITATION INSTRUCTIONS ---
    <contents of citation_<role>.txt>
    (injected only when retrieved_chunks or structured_facts are non-empty)

    USER QUERY:
    <query>

The system instruction (``system_<role>.txt``) is passed separately via
``GenerateContentConfig.system_instruction`` so it is treated as a hard
behavioural constraint, not just another input token.
"""
from __future__ import annotations

import json
import logging
import os
from functools import lru_cache # for caching loaded prompts
from pathlib import Path

logger = logging.getLogger(__name__)

# Resolved once at import time:
# services/llm/  →  services/  →  backend/  →  prompts/
_PROMPTS_DIR: Path = Path(__file__).resolve().parent.parent.parent / "prompts"

# ── Role → file mappings ──────────────────────────────────────────────────────
# To add a new role, add one entry to each dict and create the matching files.

_PROMPT_FILES: dict[str, str] = {
    "user": "system_user.txt",
    "doctor": "system_doctor.txt",
}

_CITATION_FILES: dict[str, str] = {
    "user":   "citation_user.txt",
    "doctor": "citation_doctor.txt",
}

# Fallback role used when an unknown role string is received.
_DEFAULT_ROLE: str = "user"


# ── File loaders (both cached) ────────────────────────────────────────────────

@lru_cache(maxsize=8)
def _load_prompt_file(filepath: str) -> str:
    """Read, strip, and cache the content of a single prompt file.

    Private helper shared by :func:`load_system_prompt` and
    :func:`load_citation_instructions`.  Caching is keyed on the absolute
    file path string so each unique file is read from disk at most once per
    process lifetime.

    Parameters
    ----------
    filepath:
        Absolute path to the file as a ``str`` (``lru_cache`` requires
        hashable arguments; ``Path`` objects are hashable but using ``str``
        is explicit and avoids platform edge-cases).

    Returns
    -------
    str
        File contents with leading/trailing whitespace stripped.

    Raises
    ------
    FileNotFoundError
        Re-raised with a human-readable message that names the missing file.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {path}. "
            f"Expected it at {_PROMPTS_DIR / path.name}"
        )
    text = path.read_text(encoding="utf-8").strip()
    logger.debug("Loaded prompt file '%s' (%d chars).", path.name, len(text))
    return text


def _resolve_role(role: str, file_mapping: dict[str, str]) -> str:
    """Return the canonical role key for ``file_mapping``, with fallback.

    If ``role`` is not a recognised key, logs a warning and returns
    ``_DEFAULT_ROLE`` so the pipeline continues without crashing.

    Parameters
    ----------
    role:
        The role string from ``BuiltContext.role``.
    file_mapping:
        The dict to look up (``_PROMPT_FILES`` or ``_CITATION_FILES``).

    Returns
    -------
    str
        A key guaranteed to exist in ``file_mapping``.
    """
    if role not in file_mapping:
        logger.warning(
            "Unknown role '%s'; falling back to '%s'.", role, _DEFAULT_ROLE
        )
        return _DEFAULT_ROLE
    return role


# ── Public loaders ────────────────────────────────────────────────────────────

def load_system_prompt(role: str) -> str:
    """Load and cache the system prompt for the given role.

    The system prompt defines the *behavioural persona* of the LLM: safety
    rules, output format, tone.  It is passed to the Gemini API as
    ``GenerateContentConfig.system_instruction`` — not in the user turn —
    so it is treated as a hard constraint rather than just input text.

    Delegates disk I/O to the shared :func:`_load_prompt_file` cache so each
    file is read at most once per process.

    Parameters
    ----------
    role:
        ``"user"`` (wellbeing coach) or ``"doctor"`` (clinical assistant).
        Unknown roles fall back to ``"user"`` with a warning.

    Returns
    -------
    str
        Full system-prompt text ready to pass to ``GenerateContentConfig``.

    Raises
    ------
    FileNotFoundError
        If ``prompts/system_<role>.txt`` does not exist.
    """
    canonical = _resolve_role(role, _PROMPT_FILES)
    filepath = str(_PROMPTS_DIR / _PROMPT_FILES[canonical])
    return _load_prompt_file(filepath)


def load_citation_instructions(role: str) -> str:
    """Load and cache the citation instructions for the given role.

    Citation instructions define *how to reference grounding data* in the
    LLM's response: cite format, when to add ⚠️, what to say when data is
    absent.  Unlike the system prompt they are injected into the *user turn*
    so the model sees them as part of the per-request context.

    Keeping these in ``prompts/citation_<role>.txt`` means the wording can be
    updated without any code change — important since citation formats may
    evolve as the frontend rendering changes.

    Parameters
    ----------
    role:
        ``"user"`` or ``"doctor"``.  Unknown roles fall back to ``"user"``.

    Returns
    -------
    str
        Full citation instructions text.

    Raises
    ------
    FileNotFoundError
        If ``prompts/citation_<role>.txt`` does not exist.
    """
    canonical = _resolve_role(role, _CITATION_FILES)
    filepath = str(_PROMPTS_DIR / _CITATION_FILES[canonical])
    return _load_prompt_file(filepath)


# ── Prompt assembly ───────────────────────────────────────────────────────────

def build_prompt(query: str, context_dict: dict) -> str:
    """Assemble the user-turn prompt from context data and a user query.

    This function owns **structure** and **conditional logic** only:

    * It decides *where* each block goes in the final string.
    * It decides *whether* to include the citation block (only when grounding
      data is present — injecting citation rules with nothing to cite would
      confuse the model).
    * It does **not** own the *wording* of any block — all text comes from
      the prompt files in ``prompts/``.

    The role is read from ``context_dict["role"]`` (set by
    :func:`~backend.services.context.context_builder.build_context`) so the
    correct role-specific citation file is chosen automatically without
    requiring an extra parameter.

    Prompt layout
    -------------
    ::

        MEDICAL CONTEXT DATA:
        ```json
        { ...BuiltContext serialised as indented JSON... }
        ```

        --- CITATION INSTRUCTIONS ---
        <contents of prompts/citation_<role>.txt>
        (this entire block is omitted when no grounding data is available)

        USER QUERY:
        <query>

    Parameters
    ----------
    query:
        The original user question, placed after the context block and
        separated by the ``USER QUERY:`` label to prevent prompt injection.
    context_dict:
        The serialisable ``BuiltContext`` payload (``.model_dump()`` result).
        Must contain a ``"role"`` key and optionally
        ``"rag_knowledge_base.retrieved_chunks"`` and ``"structured_facts"``.

    Returns
    -------
    str
        The complete formatted user-turn string ready to pass as the
        ``contents`` argument to a Gemini (or compatible) API client.

    Notes
    -----
    * Indented JSON (``indent=2``) helps the model reliably parse nested keys
      like ``"active_alerts"`` and ``"retrieved_chunks"`` while keeping token
      usage reasonable.
    * The citation block is loaded once per process per role (cached by
      :func:`load_citation_instructions`); repeated calls within the same
      request are essentially free.
    * If ``load_citation_instructions`` raises (e.g., missing file), a
      warning is logged and the citation block is omitted rather than
      failing the entire request.
    """
    context_str = json.dumps(context_dict, indent=2, default=str)

    # Decide whether grounding data is present.
    # Both retrieved_chunks (RAG) and structured_facts (lab results) count.
    rag_kb = context_dict.get("rag_knowledge_base") or {}
    has_grounding = bool(
        (rag_kb.get("retrieved_chunks") or [])
        or (context_dict.get("structured_facts") or [])
    )

    # Build the citation block from the role-specific file (best-effort).
    citation_block = ""
    if has_grounding:
        role = context_dict.get("role") or _DEFAULT_ROLE
        try:
            citation_text = load_citation_instructions(role)
            citation_block = (
                "--- CITATION INSTRUCTIONS ---\n"
                f"{citation_text}\n\n"
            )
        except FileNotFoundError:
            logger.warning(
                "Citation instructions file missing for role='%s'; "
                "proceeding without citation block.",
                role,
            )

    return (
        "MEDICAL CONTEXT DATA:\n"
        "```json\n"
        f"{context_str}\n"
        "```\n\n"
        f"{citation_block}"
        f"USER QUERY:\n{query}"
    )
