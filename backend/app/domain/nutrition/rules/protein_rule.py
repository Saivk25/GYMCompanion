"""`ProteinRule`: flags a logged protein intake outside a configured
`[minimum, maximum]` sanity range, in grams.
"""

from __future__ import annotations

from app.domain.nutrition.rules.context import NutritionRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_MINIMUM_PROTEIN = 50.0
_DEFAULT_MAXIMUM_PROTEIN = 250.0


class ProteinRule(Rule[NutritionRuleContext]):
    """Triggers when `context.protein` is below `minimum_protein` or
    above `maximum_protein` (50-250 g by default — a wide, generic
    single-day sanity range, this phase's own choice, not a personalized
    macro target — see `calories_rule.py`'s module docstring for why no
    such target is computed here). Passes, with no recommendation, when
    `context.protein` is `None`.
    """

    def __init__(
        self,
        *,
        minimum_protein: float = _DEFAULT_MINIMUM_PROTEIN,
        maximum_protein: float = _DEFAULT_MAXIMUM_PROTEIN,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("nutrition.protein"),
            name="Protein",
            description="Flags a logged protein intake outside the configured range.",
            severity=severity,
        )
        self._minimum_protein = minimum_protein
        self._maximum_protein = maximum_protein

    def evaluate(self, context: NutritionRuleContext) -> RuleResult:
        protein = context.protein
        if protein is None:
            return self._pass("No protein recorded.")

        if protein.value < self._minimum_protein:
            return self._fail(
                f"Protein intake of {protein.value:.0f} g is below the minimum of "
                f"{self._minimum_protein:.0f} g.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Consider adding a protein-rich food to today's remaining meals.",
                    ),
                ),
            )

        if protein.value > self._maximum_protein:
            return self._fail(
                f"Protein intake of {protein.value:.0f} g is above the maximum of "
                f"{self._maximum_protein:.0f} g.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Logged protein looks high for a full day — double-check "
                        "for duplicate entries.",
                    ),
                ),
            )

        return self._pass(
            f"Protein intake of {protein.value:.0f} g is within the "
            f"{self._minimum_protein:.0f}-{self._maximum_protein:.0f} g range."
        )
