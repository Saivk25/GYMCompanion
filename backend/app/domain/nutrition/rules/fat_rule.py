"""`FatRule`: flags a logged fat intake outside a configured
`[minimum, maximum]` sanity range, in grams.
"""

from __future__ import annotations

from app.domain.nutrition.rules.context import NutritionRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_MINIMUM_FAT = 20.0
_DEFAULT_MAXIMUM_FAT = 150.0


class FatRule(Rule[NutritionRuleContext]):
    """Triggers when `context.fat` is below `minimum_fat` or above
    `maximum_fat` (20-150 g by default — a wide, generic single-day
    sanity range, this phase's own choice, not a personalized macro
    target — see `calories_rule.py`'s module docstring for why no such
    target is computed here). Passes, with no recommendation, when
    `context.fat` is `None`.
    """

    def __init__(
        self,
        *,
        minimum_fat: float = _DEFAULT_MINIMUM_FAT,
        maximum_fat: float = _DEFAULT_MAXIMUM_FAT,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("nutrition.fat"),
            name="Fat",
            description="Flags a logged fat intake outside the configured range.",
            severity=severity,
        )
        self._minimum_fat = minimum_fat
        self._maximum_fat = maximum_fat

    def evaluate(self, context: NutritionRuleContext) -> RuleResult:
        fat = context.fat
        if fat is None:
            return self._pass("No fat recorded.")

        if fat.value < self._minimum_fat:
            return self._fail(
                f"Fat intake of {fat.value:.0f} g is below the minimum of "
                f"{self._minimum_fat:.0f} g.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Consider adding a source of healthy fats — very low fat "
                        "intake can affect hormone health over time.",
                    ),
                ),
            )

        if fat.value > self._maximum_fat:
            return self._fail(
                f"Fat intake of {fat.value:.0f} g is above the maximum of "
                f"{self._maximum_fat:.0f} g.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Logged fat looks high for a full day — double-check for "
                        "duplicate entries.",
                    ),
                ),
            )

        return self._pass(
            f"Fat intake of {fat.value:.0f} g is within the "
            f"{self._minimum_fat:.0f}-{self._maximum_fat:.0f} g range."
        )
