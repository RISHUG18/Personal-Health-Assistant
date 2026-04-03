"""Weekly health summary generator.

Orchestrates the full pipeline:
1. Gather data (wearable vitals + lab snapshot)
2. Generate two summaries via Gemini (user-facing + doctor-facing)
3. Persist both to the ``health_summaries`` Supabase table

Design
------
* Uses the **official prompt registry** (`load_system_prompt`, `build_prompt`)
  from ``services/llm/prompt_builder.py``.  Prompt content is never read
  from disk directly by this module.
* Uses the **existing data fetchers** (`fetch_wearable_vitals`,
  `fetch_user_lab_snapshot`) so data access stays in its dedicated layer.
* Follows the same graceful-degradation pattern: if wearable or lab data is
  unavailable the summary is still generated with whatever context is present.

Usage
-----
::

    from backend.services.summaries.generator import SummaryGenerator

    gen = SummaryGenerator()
    gen.generate_weekly_summaries(user_id="<uuid>")
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict, Optional

from backend.config.supabase_client import get_supabase_client
from backend.services.context.data_fetchers import (
    fetch_user_lab_snapshot,
    fetch_wearable_vitals,
)
from backend.services.llm import GeminiService, load_system_prompt, build_prompt

logger = logging.getLogger(__name__)

# Roles to generate summaries for.
_TARGET_ROLES = ("user", "doctor")

# Maps target_role → prompt-registry key used by load_system_prompt / build_prompt.
_ROLE_TO_PROMPT_KEY: Dict[str, str] = {
    "user": "summary_user",
    "doctor": "summary_doctor",
}


class SummaryGenerator:
    """Generates and stores weekly AI health summaries.

    One instance should be created per worker process (or per request — the
    class is lightweight).  The ``GeminiService`` is instantiated once and
    reused across calls.

    Parameters
    ----------
    llm:
        Optional pre-built ``GeminiService`` instance.  When omitted the
        generator creates its own (reads ``GEMINI_API_KEY`` from env).
    """

    def __init__(self, llm: Optional[GeminiService] = None) -> None:
        self._llm = llm or GeminiService()

    # ── Public API ────────────────────────────────────────────────────────────

    def generate_weekly_summaries(self, user_id: str) -> Dict[str, Any]:
        """Generate and persist weekly summaries for both roles.

        Parameters
        ----------
        user_id:
            UUID of the patient whose data will be summarised.

        Returns
        -------
        dict
            ``{"user_id": ..., "generated": [...roles...], "errors": [...]}``
        """
        # ── 1. Data gathering ─────────────────────────────────────────────────
        vitals = fetch_wearable_vitals(user_id, days=7)
        lab_snapshot = fetch_user_lab_snapshot(user_id)

        context_payload = self._build_context_payload(user_id, vitals, lab_snapshot)

        # ── 2. Generate for each target role ──────────────────────────────────
        generated: list[str] = []
        errors: list[str] = []

        for target_role in _TARGET_ROLES:
            try:
                summary_text = self._generate_for_role(
                    target_role=target_role,
                    context_payload=context_payload,
                )
                self._persist(user_id, target_role, summary_text)
                generated.append(target_role)
                logger.info(
                    "Generated '%s' summary for user_id=%s (%d chars).",
                    target_role,
                    user_id,
                    len(summary_text),
                )
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Failed to generate '%s' summary for user_id=%s: %s",
                    target_role,
                    user_id,
                    exc,
                )
                errors.append(f"{target_role}: {exc}")

        return {"user_id": user_id, "generated": generated, "errors": errors}

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _build_context_payload(
        user_id: str,
        vitals: Optional[Dict[str, Any]],
        lab_snapshot: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Package fetched data into the context dict consumed by build_prompt.

        The shape mirrors ``BuiltContext.model_dump()`` closely enough for the
        prompt builder to work correctly, without requiring a full
        ``build_context()`` call (which needs a user query and RAG chunks that
        are irrelevant for a scheduled summary).
        """
        payload: Dict[str, Any] = {
            "user_profile": {"user_id": user_id},
            "medical_snapshot": lab_snapshot.get("recent_vitals", {}),
            "structured_facts": lab_snapshot.get("raw_lab_results", []),
            "active_alerts": [], #TODO: Add active alerts
            "rag_knowledge_base": {"query_used": "weekly_summary", "retrieved_chunks": []},
            "wearable_data": vitals or {},
        }
        return payload

    def _generate_for_role(
        self,
        target_role: str,
        context_payload: Dict[str, Any],
    ) -> str:
        """Call Gemini for a single target role and return the response text."""
        prompt_key = _ROLE_TO_PROMPT_KEY[target_role]

        # Load the role-specific system prompt from the registry.
        system_prompt = load_system_prompt(prompt_key)

        # Inject the role into the context so build_prompt can resolve
        # the citation instructions correctly.
        context_with_role = {**context_payload, "role": prompt_key}

        # Assemble the user-turn prompt via the official helper.
        user_turn = build_prompt(
            query="Generate a weekly health summary based on the provided data.",
            context_dict=context_with_role,
        )

        # Call Gemini.
        return self._llm.generate(
            query=user_turn,
            context_dict=context_with_role,
            system_instruction=system_prompt,
        )

    @staticmethod
    def _persist(user_id: str, target_role: str, summary_content: str) -> None:
        """Insert a summary row into the ``health_summaries`` table."""
        client = get_supabase_client()
        client.table("health_summaries").insert({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "period_type": "weekly",
            "target_role": target_role,
            "summary_content": summary_content,
        }).execute()
