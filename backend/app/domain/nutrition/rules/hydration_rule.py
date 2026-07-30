"""`HydrationRule`: flags a logged water intake outside a configured
`[minimum, maximum]` sanity range, in milliliters.
"""

from __future__ import annotations

from app.domain.nutrition.rules.context import NutritionRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_MINIMUM_WATER_INTAKE = 1500.0
_DEFAULT_MAXIMUM_WATER_INTAKE = 6000.0


class HydrationRule(Rule[NutritionRuleContext]):
    """Triggers when `context.water_intake` is below
    `minimum_water_intake` or above `maximum_water_intake` (1500-6000 ml
    by default — a wide, generic single-day sanity range, this phase's
    own choice, not a personalized target; the upper bound guards against
    a logging error rather than modeling actual water-intoxication risk,
    which would require far more context than this rule has). Passes,
    with no recommendation, when `context.water_intake` is `None`.
    """

    def __init__(
        self,
        *,
        minimum_water_intake: float = _DEFAULT_MINIMUM_WATER_INTAKE,
        maximum_water_intake: float = _DEFAULT_MAXIMUM_WATER_INTAKE,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("nutrition.hydration"),
            name="Hydration",
            description="Flags a logged water intake outside the configured range.",
            severity=severity,
        )
        self._minimum_water_intake = minimum_water_intake
        self._maximum_water_intake = maximum_water_intake

    def evaluate(self, context: NutritionRuleContext) -> RuleResult:
        water_intake = context.water_intake
        if water_intake is None:
            return self._pass("No water intake recorded.")

        if water_intake.value < self._minimum_water_intake:
            return self._fail(
                f"Water intake of {water_intake.value:.0f} ml is below the minimum of "
                f"{self._minimum_water_intake:.0f} ml.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Consider drinking more water throughout the day.",
                    ),
                ),
            )

        if water_intake.value > self._maximum_water_intake:
            return self._fail(
                f"Water intake of {water_intake.value:.0f} ml is above the maximum of "
                f"{self._maximum_water_intake:.0f} ml.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Logged water intake looks high for a full day — double-check "
                        "for duplicate entries.",
                    ),
                ),
            )

        return self._pass(
            f"Water intake of {water_intake.value:.0f} ml is within the "
            f"{self._minimum_water_intake:.0f}-{self._maximum_water_intake:.0f} ml range."
        )
