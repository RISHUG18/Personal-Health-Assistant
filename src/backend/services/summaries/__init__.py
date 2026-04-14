"""Summaries service package — public API.

Exports
-------
SummaryGenerator
    Orchestrates periodic health summary generation for both 'user' and 'doctor'
    roles using wearable vitals, lab data, and the Gemini LLM.
SummaryTimeframe
    Shared enum for summary period selection.
get_days_for_timeframe
    Helper mapping summary period → wearable lookback days.
"""

from backend.services.summaries.generator import (
    SummaryGenerator,
    SummaryTimeframe,
    get_days_for_timeframe,
)

__all__ = ["SummaryGenerator", "SummaryTimeframe", "get_days_for_timeframe"]
