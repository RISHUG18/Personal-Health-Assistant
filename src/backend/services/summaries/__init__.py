"""Summaries service package — public API.

Exports
-------
SummaryGenerator
    Orchestrates weekly health summary generation for both 'user' and 'doctor'
    roles using wearable vitals, lab data, and the Gemini LLM.
"""

from backend.services.summaries.generator import SummaryGenerator

__all__ = ["SummaryGenerator"]
