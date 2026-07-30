"""`FiberRule`: flags a logged fiber intake outside a configured
`[minimum, maximum]` sanity range, in grams.
"""

from __future__ import annotations

from app.domain.nutrition.rules.context import NutritionRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_MINIMUM_FIBER = 15.0
_DEFAULT_MAXIMUM_FIBER = 70.0


class FiberRule(Rule[NutritionRuleContext]):
    """Triggers when `context.fiber` is below `minimum_fiber` or above
    `maximum_fiber` (15-70 g by default — a wide, generic single-day
    sanity range, this phase's own choice, not a personalized target —
    see `calories_rule.py`'s module docstring for why no such target is
    computed here; the upper bound exists mainly to catch a logging
    error, since very high fiber intake is rarely a real day's data).
    Passes, with no recommendation, when `context.fiber` is `None`.
    """

    def __init__(
        self,
        *,
        minimum_fiber: float = _DEFAULT_MINIMUM_FIBER,
        maximum_fiber: float = _DEFAULT_MAXIMUM_FIBER,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("nutrition.fiber"),
            name="Fiber",
            description="Flags a logged fiber intake outside the configured range.",
            severity=severity,
        )
        self._minimum_fiber = minimum_fiber
        self._maximum_fiber = maximum_fiber

    def evaluate(self, context: NutritionRuleContext) -> RuleResult:
        fiber = context.fiber
        if fiber is None:
            return self._pass("No fiber recorded.")

        if fiber.value < self._minimum_fiber:
            return self._fail(
                f"Fiber intake of {fiber.value:.0f} g is below the minimum of "
                f"{self._minimum_fiber:.0f} g.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Consider adding vegetables, fruit, or whole grains to "
                        "increase fiber.",
                    ),
                ),
            )

        if fiber.value > self._maximum_fiber:
            return self._fail(
                f"Fiber intake of {fiber.value:.0f} g is above the maximum of "
                f"{self._maximum_fiber:.0f} g.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Logged fiber looks high for a full day — double-check for "
                        "duplicate entries.",
                    ),
                ),
            )

        return self._pass(
            f"Fiber intake of {fiber.value:.0f} g is within the "
            f"{self._minimum_fiber:.0f}-{self._maximum_fiber:.0f} g range."
        )
