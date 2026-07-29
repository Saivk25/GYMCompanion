"""`Recommendation`: one piece of advice attached to a `RuleResult`.

Deliberately minimal — a severity and a message, nothing else. It carries
no reference back to the rule that produced it (`RuleResult.triggered_rules`
already answers "which rule," at the result level a `Recommendation` is
scoped within), and no rationale/authority-source tagging of its own (the
Domain Model & Decision Engine Bible's `Recommendation` aggregate,
Section 7.9, carries both — that is a *future*, persisted, cross-engine
aggregate arbitrating Rules/Stats/AI output together; this type is this
increment's much smaller "what does this one rule want to tell the user"
building block, not that aggregate. See
`docs/adr/0013-rule-engine-foundation.md`).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.rules.severity import RecommendationSeverity
from app.domain.shared_kernel.validation import ensure_not_empty
from app.domain.shared_kernel.value_object import ValueObject


@dataclass(frozen=True, kw_only=True)
class Recommendation(ValueObject):
    """One piece of rule-generated advice: how seriously to treat it
    (`severity`) and what it says (`message`)."""

    severity: RecommendationSeverity
    message: str

    def __post_init__(self) -> None:
        ensure_not_empty(self.message, "recommendation message")
