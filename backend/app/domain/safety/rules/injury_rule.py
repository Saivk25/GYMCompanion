"""`InjuryRule`: evaluates active injuries or rehabilitation restrictions
supplied in the context — the Product Bible's "Injury/medical screening:
structured questions plus clinician-clearance flags before risky
movement categories unlock" (MVP, "non-negotiable").

CRITICAL by default, the most severe default in this package: an injury
still marked `restricts_training=True` (no recorded clearance) is the
closest this codebase comes to the Domain Model & Decision Engine
Bible's `EscalationCase` ("blocks high-intensity Session tiers and new
Plan activation until resolved") — but see this rule's own `evaluate()`
for why it can only flag, never actually block a session; enforcing that
block is a future Plan/Session-generation concern, out of scope here.
"""

from __future__ import annotations

from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity
from app.domain.safety.rules.context import SafetyRuleContext


class InjuryRule(Rule[SafetyRuleContext]):
    """Triggers (CRITICAL by default) whenever any `ActiveInjury` in
    `context.active_injuries` has `restricts_training=True`. Passes,
    naming any non-restricting injuries still on file, when
    `active_injuries` is non-empty but none restrict training; passes
    with "no active injuries" when it's empty."""

    def __init__(
        self,
        *,
        severity: RecommendationSeverity = RecommendationSeverity.CRITICAL,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("safety.injury"),
            name="Injury",
            description="Evaluates active injuries or rehabilitation restrictions on file.",
            severity=severity,
        )

    def evaluate(self, context: SafetyRuleContext) -> RuleResult:
        injuries = context.active_injuries
        if not injuries:
            return self._pass("No active injuries or rehabilitation restrictions declared.")

        restricting = [injury for injury in injuries if injury.restricts_training]
        if restricting:
            descriptions = "; ".join(injury.description for injury in restricting)
            return self._fail(
                f"{len(restricting)} active injury/injuries still restrict training: "
                f"{descriptions}.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="An active injury restricts training — avoid the affected "
                        "movement pattern until cleared.",
                    ),
                ),
            )

        descriptions = "; ".join(injury.description for injury in injuries)
        return self._pass(
            f"{len(injuries)} injury/injuries on file, none currently restricting training: "
            f"{descriptions}."
        )
