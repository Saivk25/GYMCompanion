"""`ProgressionStageRule`: a soft bias against `Difficulty.ADVANCED` (and,
more mildly, `Difficulty.INTERMEDIATE`) candidates when the user's
logged training history is thin — no Product Bible table names this
rule directly (Table 48 is silent on difficulty-vs-experience fit), so
this is this phase's own scoped judgment call, deliberately narrow to
avoid fabricating an unfounded scheme.

Deliberately asks a *different* question from every rule in
`app.domain.workout.rules` (Progressive Overload): this rule counts how
many `WorkoutSessionSummary` entries exist in the supplied
`ProgressiveOverloadRuleContext` — a simple, undisputed fact — rather
than asking whether volume/intensity is trending up, plateaued, or
declining, which is exclusively `VolumeRule`/`IntensityRule`/
`ProgressionRule`/`DeloadRule`'s own domain. Reading the same
`sessions` tuple those rules also read, for a question they never ask,
is what keeps this rule from duplicating their decision logic — see
`docs/adr/0021-exercise-recommendation-composes-rule-outputs.md`.

Always passes — a thin training history is a reason for a *softer*
recommendation, not an exclusion.
"""

from __future__ import annotations

from app.domain.exercise.enums import Difficulty
from app.domain.exercise.rules.context import ExerciseRecommendationRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_INTERMEDIATE_MINIMUM_SESSIONS = 4
_DEFAULT_ADVANCED_MINIMUM_SESSIONS = 12


class ProgressionStageRule(Rule[ExerciseRecommendationRuleContext]):
    """Attaches an ADVISORY recommendation when the candidate exercise's
    `difficulty` is `INTERMEDIATE`/`ADVANCED` and the supplied
    `progressive_overload` context's session count falls below that
    difficulty's configured minimum. Passes, with no recommendation,
    for `Difficulty.BEGINNER` (always considered appropriate), when the
    minimum is already met, or when no `progressive_overload` context
    was supplied at all. Never fails.
    """

    def __init__(
        self,
        *,
        intermediate_minimum_sessions: int = _DEFAULT_INTERMEDIATE_MINIMUM_SESSIONS,
        advanced_minimum_sessions: int = _DEFAULT_ADVANCED_MINIMUM_SESSIONS,
        severity: RecommendationSeverity = RecommendationSeverity.ADVISORY,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("exercise_recommendation.progression_stage"),
            name="Progression Stage",
            description=("Biases exercise selection toward the user's current progression stage."),
            severity=severity,
        )
        self._intermediate_minimum_sessions = intermediate_minimum_sessions
        self._advanced_minimum_sessions = advanced_minimum_sessions

    def evaluate(self, context: ExerciseRecommendationRuleContext) -> RuleResult:
        difficulty = context.exercise.difficulty
        if difficulty is Difficulty.BEGINNER:
            return self._pass("Beginner-level exercises are appropriate at any stage.")

        history = context.progressive_overload
        if history is None:
            return self._pass(
                "No training history supplied; cannot evaluate progression stage fit."
            )

        session_count = len(history.sessions)
        minimum = (
            self._advanced_minimum_sessions
            if difficulty is Difficulty.ADVANCED
            else self._intermediate_minimum_sessions
        )
        if session_count < minimum:
            return self._pass(
                f"Training history ({session_count} session(s)) is below the {minimum} "
                f"typically expected before a {difficulty.value} exercise is well-supported "
                "by evidence.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message=f"Training history is still limited ({session_count} "
                        f"session(s)) — confirm this {difficulty.value} exercise feels "
                        "appropriate, or consider an easier alternative.",
                    ),
                ),
            )

        return self._pass(
            f"Training history ({session_count} session(s)) supports this exercise's "
            f"{difficulty.value} difficulty."
        )
