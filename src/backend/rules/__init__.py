"""Rules engine package.

Public API
----------
evaluate_rules(client, user_id)           → List[AlertRecord]
persist_alerts(client, user_id, alerts)   → dict
ALL_RULES                                 → List[RuleDefinition]

Typical usage
-------------
    from backend.rules import evaluate_rules, persist_alerts

    alerts = evaluate_rules(client, user_id)
    result = persist_alerts(client, user_id, alerts)
"""

from .definitions import ALL_RULES, LabRow, RuleDefinition
from .engine import evaluate_rules
from .inserter import persist_alerts
from .models import AlertRecord, EvidenceRef, RuleResult, Severity

__all__ = [
    # Registry
    "ALL_RULES",
    "RuleDefinition",
    "LabRow",
    # Engine
    "evaluate_rules",
    # Persistence
    "persist_alerts",
    # Models
    "AlertRecord",
    "EvidenceRef",
    "RuleResult",
    "Severity",
]
