"""`ContraindicationRule`: surfaces declared movement restrictions or
exercise contraindications on file for the user.

Scoped narrowly on purpose: this rule can only say "these restrictions
are on file", never "this specific exercise is unsafe" — matching a
prescribed exercise against `context.declared_restrictions` (the way the
Domain Model & Decision Engine Bible's own "Contraindication gate", Table
48, matches `Exercise.contraindication_tags` against an active
`SafetyFlag` to remove candidates before ranking) requires an actual
exercise candidate list, which is an Exercise Recommendation /
Substitution concern this phase explicitly excludes
(`Do NOT implement: Exercise substitution`). Triggers as an ADVISORY
reminder, not a training block — the restriction itself isn't unsafe to
merely have on file; what would be unsafe is training in violation of
it, which this rule has no way to check without an exercise selection to
evaluate against.
"""

from __future__ import annotations

from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity
from app.domain.safety.rules.context import SafetyRuleContext


class ContraindicationRule(Rule[SafetyRuleContext]):
    """Triggers (ADVISORY by default) whenever `context.declared_restrictions`
    is non-empty, listing every restriction's tag in the explanation and
    recommendation. Passes when no restrictions are declared."""

    def __init__(
        self,
        *,
        severity: RecommendationSeverity = RecommendationSeverity.ADVISORY,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("safety.contraindication"),
            name="Contraindication",
            description="Surfaces declared movement restrictions or exercise contraindications.",
            severity=severity,
        )

    def evaluate(self, context: SafetyRuleContext) -> RuleResult:
        restrictions = context.declared_restrictions
        if not restrictions:
            return self._pass("No declared movement restrictions or contraindications on file.")

        tags = ", ".join(restriction.tag for restriction in restrictions)
        return self._fail(
            f"{len(restrictions)} declared restriction(s) on file: {tags}.",
            recommendations=(
                Recommendation(
                    severity=self.severity,
                    message="Avoid exercises that conflict with the declared restriction(s): "
                    f"{tags}.",
                ),
            ),
        )
