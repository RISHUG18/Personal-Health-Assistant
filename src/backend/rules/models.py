"""Pydantic models for the rules engine.

These models are the internal contract between the rule definitions,
the evaluation engine, and the persistence layer.  Nothing in this file
touches the database — it is pure data-shape code.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Operational severity of a triggered alert.

    LOW    — informational; good to know but not urgent
    MEDIUM — warrants attention at next routine check
    HIGH   — should be reviewed promptly
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EvidenceRef(BaseModel):
    """A pointer to a single piece of verifiable evidence.

    All three fields are optional individually, but at least one of
    ``report_id`` or ``lab_result_id`` should be populated.
    """

    report_id: Optional[str] = Field(
        None, description="UUID of the parent medical_reports row"
    )
    lab_result_id: Optional[str] = Field(
        None, description="UUID of the specific lab_results row"
    )
    ocr_text_snippet: Optional[str] = Field(
        None, description="Short verbatim line from OCR text (≤ 200 chars)"
    )


class RuleResult(BaseModel):
    """Outcome produced by evaluating one rule against a user's data.

    The engine only produces an alert when ``triggered`` is True.
    """

    rule_id: str = Field(..., description="Unique slug identifying the rule")
    triggered: bool = Field(..., description="Whether the rule condition was met")
    severity: Optional[Severity] = Field(
        None, description="Severity of the alert (only set when triggered=True)"
    )
    reason: Optional[str] = Field(
        None,
        description="Human-readable explanation of why the rule fired "
        "(only set when triggered=True)",
    )
    evidence_refs: List[EvidenceRef] = Field(
        default_factory=list,
        description="DB record references that justify this alert",
    )


class AlertRecord(BaseModel):
    """A fully formed alert ready to be written to the database.

    Created by the engine from a triggered RuleResult; consumed by the
    persistence layer.
    """

    alert_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="UUID for the alerts.id column",
    )
    user_id: str = Field(..., description="UUID of the user who owns this alert")
    severity: Severity = Field(..., description="Severity level")
    reason: str = Field(..., description="Human-readable alert description")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of alert creation",
    )
    evidence_refs: List[EvidenceRef] = Field(
        default_factory=list,
        description="Evidence that will be persisted in alert_evidence",
    )
