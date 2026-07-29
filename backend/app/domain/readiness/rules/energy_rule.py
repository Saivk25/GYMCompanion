"""`EnergyRule`: flags a subjective energy level below a configured
minimum on the 1-10 scale `app.domain.readiness.value_objects.EnergyLevel`
uses.
"""

from __future__ import annotations

from app.domain.readiness.rules.context import ReadinessRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_MINIMUM_ENERGY = 4


class EnergyRule(Rule[ReadinessRuleContext]):
    """Triggers when `context.energy_level` is below `minimum_energy`
    (4 out of 10 by default — this phase's own choice: low enough that it
    flags a genuinely low-energy day, not every day below the scale's
    midpoint). Passes, with no recommendation, when `context.energy_level`
    is `None`.
    """

    def __init__(
        self,
        *,
        minimum_energy: int = _DEFAULT_MINIMUM_ENERGY,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("readiness.energy_level"),
            name="Energy Level",
            description="Flags a subjective energy level below the configured minimum.",
            severity=severity,
        )
        self._minimum_energy = minimum_energy

    def evaluate(self, context: ReadinessRuleContext) -> RuleResult:
        energy_level = context.energy_level
        if energy_level is None:
            return self._pass("No energy level recorded.")

        if energy_level.value >= self._minimum_energy:
            return self._pass(
                f"Energy level of {energy_level.value} meets the minimum of {self._minimum_energy}."
            )

        return self._fail(
            f"Energy level of {energy_level.value} is below the minimum of {self._minimum_energy}.",
            recommendations=(
                Recommendation(
                    severity=self.severity,
                    message="Consider a lighter session or an extra rest day today.",
                ),
            ),
        )
