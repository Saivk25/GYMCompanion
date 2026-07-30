"""`CarbohydratesRule`: flags a logged carbohydrate intake outside a
configured `[minimum, maximum]` sanity range, in grams.
"""

from __future__ import annotations

from app.domain.nutrition.rules.context import NutritionRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_MINIMUM_CARBOHYDRATES = 50.0
_DEFAULT_MAXIMUM_CARBOHYDRATES = 400.0


class CarbohydratesRule(Rule[NutritionRuleContext]):
    """Triggers when `context.carbohydrates` is below
    `minimum_carbohydrates` or above `maximum_carbohydrates` (50-400 g by
    default — a wide, generic single-day sanity range, this phase's own
    choice, not a personalized macro target — see `calories_rule.py`'s
    module docstring for why no such target is computed here). Passes,
    with no recommendation, when `context.carbohydrates` is `None`.
    """

    def __init__(
        self,
        *,
        minimum_carbohydrates: float = _DEFAULT_MINIMUM_CARBOHYDRATES,
        maximum_carbohydrates: float = _DEFAULT_MAXIMUM_CARBOHYDRATES,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("nutrition.carbohydrates"),
            name="Carbohydrates",
            description="Flags a logged carbohydrate intake outside the configured range.",
            severity=severity,
        )
        self._minimum_carbohydrates = minimum_carbohydrates
        self._maximum_carbohydrates = maximum_carbohydrates

    def evaluate(self, context: NutritionRuleContext) -> RuleResult:
        carbohydrates = context.carbohydrates
        if carbohydrates is None:
            return self._pass("No carbohydrates recorded.")

        if carbohydrates.value < self._minimum_carbohydrates:
            return self._fail(
                f"Carbohydrate intake of {carbohydrates.value:.0f} g is below the minimum of "
                f"{self._minimum_carbohydrates:.0f} g.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Consider adding a carbohydrate source to fuel training "
                        "and recovery.",
                    ),
                ),
            )

        if carbohydrates.value > self._maximum_carbohydrates:
            return self._fail(
                f"Carbohydrate intake of {carbohydrates.value:.0f} g is above the maximum of "
                f"{self._maximum_carbohydrates:.0f} g.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Logged carbohydrates look high for a full day — double-check "
                        "for duplicate entries.",
                    ),
                ),
            )

        return self._pass(
            f"Carbohydrate intake of {carbohydrates.value:.0f} g is within the "
            f"{self._minimum_carbohydrates:.0f}-{self._maximum_carbohydrates:.0f} g range."
        )
