"""`ContraindicatedExerciseRule`: the literal, exercise-level
"Contraindication gate" Domain Model & Decision Engine Bible Table 48
names — "An Exercise's contraindication_tags match an active
SafetyFlag... Removed from candidates before ranking, not just
deprioritized."

This is exactly the gate `docs/adr/0018-safety-rule-engine-composition-
and-authority.md`'s Consequences section named as future scope:
Safety's own `ContraindicationRule` "can only say a restriction is on
file, never that a specific exercise violates it." This rule is that
missing piece — it reuses `DeclaredRestriction`
(`app.domain.safety.rules.context`) directly rather than redefining an
equivalent type, and compares its `tag` against the candidate
`Exercise`'s own `contraindications.tags`.

Also composes `safety_result` as a broad override: if the supplied
`SafetyRuleEngine` verdict is `CRITICAL`, no exercise is recommended
regardless of tag-level matching — "conflict with safety restrictions"
read broadly, not only at the tag level. This reads Safety's own
already-computed severity, it never re-evaluates any Safety rule
itself — see this package's own `context.py` docstring and
`docs/adr/0021-exercise-recommendation-composes-rule-outputs.md`.
"""

from __future__ import annotations

from app.domain.exercise.rules.context import ExerciseRecommendationRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity


class ContraindicatedExerciseRule(Rule[ExerciseRecommendationRuleContext]):
    """Fails (excludes) when the candidate exercise's contraindication
    tags overlap any declared restriction's tag, or when the supplied
    `safety_result` is `RecommendationSeverity.CRITICAL`. Passes, with
    an explanation, when neither applies, or when no restriction data
    was supplied at all.
    """

    def __init__(
        self,
        *,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("exercise_recommendation.contraindicated_exercise"),
            name="Contraindicated Exercise",
            description="Excludes exercises that conflict with declared safety restrictions.",
            severity=severity,
        )

    def evaluate(self, context: ExerciseRecommendationRuleContext) -> RuleResult:
        safety_result = context.safety_result
        if safety_result is not None and safety_result.severity is RecommendationSeverity.CRITICAL:
            return self._fail(
                "Safety evaluation is currently CRITICAL; no exercise is recommended.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="A critical safety finding is active — resolve it before "
                        "resuming training.",
                    ),
                ),
            )

        restriction_tags = {restriction.tag for restriction in context.declared_restrictions}
        if not restriction_tags:
            return self._pass("No declared restrictions on file.")

        matched_tags = restriction_tags & context.exercise.contraindications.tags
        if matched_tags:
            listed = ", ".join(sorted(matched_tags))
            return self._fail(
                f"This exercise's contraindication tags overlap declared restriction(s): {listed}.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message=f"Excluded — conflicts with declared restriction(s): {listed}.",
                    ),
                ),
            )

        return self._pass(
            "No overlap between declared restrictions and this exercise's contraindication tags."
        )
