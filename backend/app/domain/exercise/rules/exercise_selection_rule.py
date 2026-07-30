"""`ExerciseSelectionRule`: a soft bias toward exercises that fit the
user's current active goal and current readiness — never an exclusion.

Deliberately narrow on goal-type fit: rather than a fabricated full
mapping of every `GoalType` to every `MovementPattern` (an unfounded,
contestable opinion this codebase's engineering principles argue
against speculating on), this rule only nudges the two pairings with a
genuinely defensible, common-sense basis — `STRENGTH` goals toward
non-`CARDIO` compound patterns, `ENDURANCE` goals toward `CARDIO` — and
stays neutral for every other `GoalType`/`MovementPattern` combination.
This is this phase's own scoped judgment call, not a Product Bible
quotation (the Bible names no goal-type-to-movement-pattern mapping
anywhere). See `docs/adr/0021-exercise-recommendation-composes-rule-
outputs.md`.

Always passes — `passed=True`, `triggered_rules=()` — with an optional
attached `Recommendation` when a bias applies. This is the "soft bias,
not a gate" half of Domain Model & Decision Engine Bible Table 48's own
two-tier philosophy ("Push/pull balance... biases substitution ranking"
vs. "Contraindication gate... removed from candidates"); `RuleResult`
already models this distinction with no new field needed — a passing
result with recommendations attached, exactly the shape `Rule._pass()`
already supports.

Exercise lifecycle filtering (`ExerciseStatus.ACTIVE` vs. `DEPRECATED`)
is deliberately out of scope for this rule — the Bible's Table 48 names
no such gate, and this package trusts the application layer to only
ever construct a context for exercises worth considering in the first
place, the same trust every prior phase places in its supplied inputs.
"""

from __future__ import annotations

from app.domain.exercise.enums import MovementPattern
from app.domain.exercise.rules.context import ExerciseRecommendationRuleContext
from app.domain.goal.enums import GoalStatus, GoalType
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_STRENGTH_ORIENTED_PATTERNS = frozenset(
    {
        MovementPattern.PUSH,
        MovementPattern.PULL,
        MovementPattern.HINGE,
        MovementPattern.SQUAT,
        MovementPattern.LUNGE,
    }
)


class ExerciseSelectionRule(Rule[ExerciseRecommendationRuleContext]):
    """Attaches an ADVISORY recommendation when the candidate exercise's
    `movement_pattern` runs against a `STRENGTH`/`ENDURANCE` active
    goal's grain, or when supplied `readiness_result` is not passing.
    Never fails.
    """

    def __init__(
        self,
        *,
        severity: RecommendationSeverity = RecommendationSeverity.ADVISORY,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("exercise_recommendation.exercise_selection"),
            name="Exercise Selection",
            description="Biases exercise selection toward the user's current active goal.",
            severity=severity,
        )

    def evaluate(self, context: ExerciseRecommendationRuleContext) -> RuleResult:
        goal_recommendation = self._goal_fit_recommendation(context)
        if goal_recommendation is not None:
            return self._pass(
                f"Movement pattern {context.exercise.movement_pattern.value!r} noted against "
                "the active goal.",
                recommendations=(goal_recommendation,),
            )

        if context.readiness_result is not None and not context.readiness_result.passed:
            return self._pass(
                "Readiness evidence is currently not passing.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Readiness is currently low — consider an easier variation "
                        "of this exercise today.",
                    ),
                ),
            )

        return self._pass("No goal- or readiness-based bias applies to this exercise right now.")

    def _goal_fit_recommendation(
        self, context: ExerciseRecommendationRuleContext
    ) -> Recommendation | None:
        goal = context.goal
        if goal is None or goal.status is not GoalStatus.ACTIVE:
            return None

        pattern = context.exercise.movement_pattern
        if goal.goal_type is GoalType.STRENGTH and pattern is MovementPattern.CARDIO:
            return Recommendation(
                severity=self.severity,
                message="This is a cardio movement — for a strength goal, a compound "
                "strength exercise is usually more appropriate.",
            )
        if goal.goal_type is GoalType.ENDURANCE and pattern in _STRENGTH_ORIENTED_PATTERNS:
            return Recommendation(
                severity=self.severity,
                message="For an endurance goal, prioritizing cardio work is usually more "
                "appropriate than this movement pattern.",
            )
        return None
