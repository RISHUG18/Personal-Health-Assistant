"""Gemini LLM Service — concrete implementation of :class:`LLMProvider`.

This module is the single bridge between the assembled :class:`BuiltContext`
payload and Google's Gemini API.  It implements the :class:`LLMProvider`
protocol so it can be swapped for any other back-end (e.g., OpenAI, local
Ollama) without changing the calling code.

Environment
-----------
The service reads ``GEMINI_API_KEY`` from the process environment at
construction time.  In production this is injected via a ``.env`` file loaded
by ``python-dotenv`` in ``main.py``; in tests it can be patched with
``monkeypatch.setenv``.

Usage
-----
::

    from backend.services.llm.gemini_service import GeminiService
    from backend.services.llm.prompt_builder import load_system_prompt

    svc = GeminiService()                          # reads GEMINI_API_KEY
    system_prompt = load_system_prompt(role="user")
    answer = svc.generate(
        query="Why is my iron low?",
        context_dict=context.model_dump(),
        system_instruction=system_prompt,
    )
"""
from __future__ import annotations

import logging
import os

from google import genai
from google.genai import types

from backend.services.llm.interfaces import LLMProvider
from backend.services.llm.prompt_builder import build_prompt

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

# Kept as a module constant so it can be overridden in tests without
# subclassing.
DEFAULT_MODEL: str = "gemini-2.5-flash"

# Temperature 0.1 forces near-deterministic, factual output — essential for
# a medical assistant where "creativity" means potential hallucinations.
_TEMPERATURE: float = 0.1


class GeminiService:
    """Concrete LLM provider backed by Google Gemini.

    Implements the :class:`~backend.services.llm.interfaces.LLMProvider`
    protocol.  Each instance holds a single authenticated
    :class:`google.genai.Client` so connection overhead is paid only once,
    not on every request.

    Parameters
    ----------
    model_name:
        Gemini model identifier.  Defaults to ``gemini-2.5-flash``.
    api_key:
        Gemini API key.  If omitted the constructor reads ``GEMINI_API_KEY``
        from the environment.

    Raises
    ------
    RuntimeError
        If ``GEMINI_API_KEY`` is absent from both the argument and the
        environment (fail-fast at construction, not at first request).
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        api_key: str | None = None,
    ) -> None:
        self.model_name = model_name

        # Resolve API key: explicit argument first, then environment variable.
        resolved_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not resolved_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. "
                "Add it to your .env file or export it in the shell."
            )

        # Instantiate the client once.  The SDK uses the key from the
        # constructor argument rather than only reading os.environ each time,
        # allowing isolated test instances with different keys.
        try:
            self._client = genai.Client(api_key=resolved_key)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to initialise Gemini client: {exc}"
            ) from exc

        logger.info(
            "GeminiService ready (model=%s).", self.model_name
        )

    # ── LLMProvider protocol ──────────────────────────────────────────────────

    def generate(
        self,
        *,
        query: str,
        context_dict: dict,
        system_instruction: str,
    ) -> str:
        """Generate a grounded, evidence-based response using Gemini.

        Workflow
        --------
        1. **Prompt construction** — delegates to :func:`build_prompt` to
           serialize the context dict into an indented JSON block followed by
           the user query.  Context is never concatenated with the system
           instruction at this stage; they are passed as separate ``config``
           and ``contents`` arguments so the model reliably distinguishes
           behavioural rules from input data.
        2. **GenerateContentConfig** — sets ``system_instruction`` (the role-
           specific rules) and ``temperature=0.1`` (near-deterministic output).
        3. **API call** — ``client.models.generate_content()`` is synchronous;
           exceptions bubble up as ``RuntimeError`` with a human-readable
           message so the route layer can return a clean HTTP 502.
        4. **Safety check** — an empty or blocked response raises immediately
           rather than silently returning ``None``.

        Parameters
        ----------
        query:
            The original user question, verbatim.
        context_dict:
            Serialisable ``BuiltContext`` payload (``.model_dump()`` result).
        system_instruction:
            Full role-specific system prompt loaded by
            :func:`~backend.services.llm.prompt_builder.load_system_prompt`.

        Returns
        -------
        str
            Markdown-formatted response from Gemini.

        Raises
        ------
        RuntimeError
            On API error, timeout, empty/blocked response, or any other
            failure.  The original exception is chained via ``__cause__`` for
            traceability.
        """
        # Build the formatted user-turn prompt (context JSON + query).
        prompt = build_prompt(query=query, context_dict=context_dict)

        # Configure generation: system prompt + low temperature for safety.
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            # Low temperature: factual, citation-grounded output only.
            # Range: 0.0 (fully deterministic) to 1.0 (creative).
            temperature=_TEMPERATURE,
        )

        logger.info(
            "Calling Gemini API (model=%s) for query: '%s...'",
            self.model_name,
            query[:60],
        )

        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
        except Exception as exc:
            logger.error("Gemini API call failed: %s", exc)
            raise RuntimeError(f"Failed to call Gemini API: {exc}") from exc

        # Guard: an empty or safety-blocked response must be reported clearly.
        response_text: str | None = getattr(response, "text", None)
        if not response_text:
            # Log finish_reason when available for debugging why Gemini stopped.
            finish_reason = _extract_finish_reason(response)
            logger.error(
                "Gemini returned an empty response. finish_reason=%s", finish_reason
            )
            raise RuntimeError(
                f"Gemini returned an empty response (finish_reason={finish_reason}). "
                "The request may have been blocked by safety filters or the context "
                "exceeded the model's token limit."
            )

        logger.info(
            "Gemini response received (%d chars).", len(response_text)
        )
        return response_text


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_finish_reason(response: object) -> str:
    """Safely extract the finish_reason string from a Gemini response object.

    ``finish_reason`` is nested inside ``response.candidates[0].finish_reason``
    for the current SDK.  This helper avoids AttributeError if the structure
    changes between SDK versions.

    Parameters
    ----------
    response:
        A ``GenerateContentResponse`` (or any object) returned by the client.

    Returns
    -------
    str
        The finish reason string, or ``"unknown"`` if not accessible.
    """
    try:
        candidates = getattr(response, "candidates", None) or []
        if candidates:
            reason = getattr(candidates[0], "finish_reason", None)
            return str(reason) if reason is not None else "unknown"
    except Exception:  # noqa: BLE001
        pass
    return "unknown"
