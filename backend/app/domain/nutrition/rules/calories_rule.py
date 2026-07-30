"""`CaloriesRule`: flags a logged calorie intake outside a configured
`[minimum, maximum]` sanity range.

A fixed range, not a personalized target — "no personalized calorie
targets" is this phase's own explicit exclusion (the Domain Model &
Decision Engine Bible's `MacroFactor`-equivalent adaptive calculation from
real intake and weight trend, Product Bible Section on Nutrition, is
deliberately not built here). This rule can only say "this number looks
implausible for a single day," never "this number is wrong for you."
"""

from __future__ import annotations

from app.domain.nutrition.rules.context import NutritionRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_MINIMUM_CALORIES = 1200.0
_DEFAULT_MAXIMUM_CALORIES = 4000.0


class CaloriesRule(Rule[NutritionRuleContext]):
    """Triggers when `context.calories` is below `minimum_calories` or
    above `maximum_calories` (1200-4000 kcal by default — a wide,
    generic single-day sanity range, this phase's own choice, not a
    Bible-mandated or personalized figure). Passes, with no
    recommendation, when `context.calories` is `None`.
    """

    def __init__(
        self,
        *,
        minimum_calories: float = _DEFAULT_MINIMUM_CALORIES,
        maximum_calories: float = _DEFAULT_MAXIMUM_CALORIES,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("nutrition.calories"),
            name="Calories",
            description="Flags a logged calorie intake outside the configured range.",
            severity=severity,
        )
        self._minimum_calories = minimum_calories
        self._maximum_calories = maximum_calories

    def evaluate(self, context: NutritionRuleContext) -> RuleResult:
        calories = context.calories
        if calories is None:
            return self._pass("No calories recorded.")

        if calories.value < self._minimum_calories:
            return self._fail(
                f"Calorie intake of {calories.value:.0f} kcal is below the minimum of "
                f"{self._minimum_calories:.0f} kcal.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Logged intake looks low for a full day — double-check "
                        "for missing entries.",
                    ),
                ),
            )

        if calories.value > self._maximum_calories:
            return self._fail(
                f"Calorie intake of {calories.value:.0f} kcal is above the maximum of "
                f"{self._maximum_calories:.0f} kcal.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Logged intake looks high for a full day — double-check "
                        "for duplicate entries.",
                    ),
                ),
            )

        return self._pass(
            f"Calorie intake of {calories.value:.0f} kcal is within the "
            f"{self._minimum_calories:.0f}-{self._maximum_calories:.0f} kcal range."
        )
