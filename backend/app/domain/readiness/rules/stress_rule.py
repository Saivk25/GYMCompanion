"""`StressRule`: flags a subjective stress level above a configured
maximum on the 1-10 scale `app.domain.readiness.value_objects.StressLevel`
uses.
"""

from __future__ import annotations

from app.domain.readiness.rules.context import ReadinessRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_MAXIMUM_STRESS = 7


class StressRule(Rule[ReadinessRuleContext]):
    """Triggers when `context.stress_level` is above `maximum_stress`
    (7 out of 10 by default — this phase's own choice, the mirror image of
    `EnergyRule`'s minimum). Passes, with no recommendation, when
    `context.stress_level` is `None`.
    """

    def __init__(
        self,
        *,
        maximum_stress: int = _DEFAULT_MAXIMUM_STRESS,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("readiness.stress_level"),
            name="Stress Level",
            description="Flags a subjective stress level above the configured maximum.",
            severity=severity,
        )
        self._maximum_stress = maximum_stress

    def evaluate(self, context: ReadinessRuleContext) -> RuleResult:
        stress_level = context.stress_level
        if stress_level is None:
            return self._pass("No stress level recorded.")

        if stress_level.value <= self._maximum_stress:
            return self._pass(
                f"Stress level of {stress_level.value} is within the maximum of "
                f"{self._maximum_stress}."
            )

        return self._fail(
            f"Stress level of {stress_level.value} exceeds the maximum of {self._maximum_stress}.",
            recommendations=(
                Recommendation(
                    severity=self.severity,
                    message="Consider a short recovery or mindfulness break today.",
                ),
            ),
        )
