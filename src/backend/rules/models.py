"""Data models for the Vitalis rules engine."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Severity(Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


@dataclass
class AlertRecord:
    """Result of evaluating a single rule.

    ``triggered=True`` means the rule fired and an alert should be stored.
    ``evidence`` is a list of :class:`~backend.rules.definitions.LabRow` objects
    that caused the rule to fire; used by the inserter to populate
    ``alert_evidence`` rows.
    """

    rule_id:   str
    triggered: bool
    severity:  Optional[Severity] = None
    reason:    Optional[str]      = None
    evidence:  list               = field(default_factory=list)  # List[LabRow]
    environmental_evidence: Optional[dict] = None  # JSON evidence mapping to environmental impact
