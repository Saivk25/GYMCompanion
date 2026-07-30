"""`EquipmentRule`: the literal "Equipment mismatch" gate Domain Model &
Decision Engine Bible Table 48 names — "A prescribed exercise's
equipment_requirements don't match the active Context. Auto-triggers
the Substitution workflow (6.3)." This engine does not build the
Substitution workflow (explicitly out of scope, per this phase's own
task) — it only produces the same underlying finding a future
Substitution workflow would consume.

No `EnvironmentContext` aggregate exists yet (Domain Model & Decision
Engine Bible, Section 4.3) to source "what equipment is currently
available" from, so `context.available_equipment` is trusted as
supplied by the application layer — the same trust `TrainingLoadSummary`
places in its caller (`docs/adr/0020-training-load-supplied-
summaries.md`), reusing `Exercise`'s own `EquipmentRequirement` value
object rather than defining an equivalent new type.
"""

from __future__ import annotations

from app.domain.exercise.rules.context import ExerciseRecommendationRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity


class EquipmentRule(Rule[ExerciseRecommendationRuleContext]):
    """Fails (excludes) when the candidate exercise requires equipment
    absent from `context.available_equipment`. Passes, with an
    explanation, when every required item is available (a bodyweight
    exercise, whose `equipment_requirements` is empty, always passes),
    or when `available_equipment` was not supplied at all.
    """

    def __init__(
        self,
        *,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("exercise_recommendation.equipment"),
            name="Equipment",
            description="Excludes exercises that require equipment that is not available.",
            severity=severity,
        )

    def evaluate(self, context: ExerciseRecommendationRuleContext) -> RuleResult:
        available = context.available_equipment
        if available is None:
            return self._pass("No equipment availability supplied; cannot evaluate.")

        missing = context.exercise.equipment_requirements - available
        if missing:
            listed = ", ".join(sorted(item.value for item in missing))
            return self._fail(
                f"This exercise requires equipment that is not available: {listed}.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message=f"Excluded — requires unavailable equipment: {listed}.",
                    ),
                ),
            )

        return self._pass("All required equipment is available.")
