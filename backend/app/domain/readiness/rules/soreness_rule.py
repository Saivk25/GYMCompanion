"""`SorenessRule`: flags a subjective soreness level above a configured
maximum on the 1-10 scale
`app.domain.readiness.value_objects.SorenessLevel` uses.
"""

from __future__ import annotations

from app.domain.readiness.rules.context import ReadinessRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_MAXIMUM_SORENESS = 7


class SorenessRule(Rule[ReadinessRuleContext]):
    """Triggers when `context.soreness_level` is above `maximum_soreness`
    (7 out of 10 by default — this phase's own choice, the same shape as
    `StressRule`'s maximum). Passes, with no recommendation, when
    `context.soreness_level` is `None`.
    """

    def __init__(
        self,
        *,
        maximum_soreness: int = _DEFAULT_MAXIMUM_SORENESS,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("readiness.soreness_level"),
            name="Soreness Level",
            description="Flags a subjective soreness level above the configured maximum.",
            severity=severity,
        )
        self._maximum_soreness = maximum_soreness

    def evaluate(self, context: ReadinessRuleContext) -> RuleResult:
        soreness_level = context.soreness_level
        if soreness_level is None:
            return self._pass("No soreness level recorded.")

        if soreness_level.value <= self._maximum_soreness:
            return self._pass(
                f"Soreness level of {soreness_level.value} is within the maximum of "
                f"{self._maximum_soreness}."
            )

        return self._fail(
            f"Soreness level of {soreness_level.value} exceeds the maximum of "
            f"{self._maximum_soreness}.",
            recommendations=(
                Recommendation(
                    severity=self.severity,
                    message="Consider lighter loading or extra warm-up for affected muscle groups.",
                ),
            ),
        )
