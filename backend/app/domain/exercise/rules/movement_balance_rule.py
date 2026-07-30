"""`MovementBalanceRule`: a soft bias toward whichever of `PUSH`/`PULL`
is currently under-represented in recent training — Domain Model &
Decision Engine Bible Table 48's "Push/pull balance... biases
substitution ranking toward pulling movements," generalized to bias
toward either direction, not only toward pulling.

The Bible's literal rule compares *push volume* to *pull volume* over a
7-day window. No context this package can reference carries that
granularity — `WorkoutSessionSummary`
(`app.domain.workout.rules.context`) is deliberately whole-session
volume only (ADR 0017), with no per-movement-pattern breakdown. This
rule's stated simplification is to count movement-pattern
*occurrences* in `context.recent_movement_patterns` (a flat tally the
application layer supplies) rather than volume — a real, documented
gap from the Bible's literal wording, the same category of gap ADR
0017 already accepts for `WorkoutSessionSummary` itself. See
`docs/adr/0021-exercise-recommendation-composes-rule-outputs.md`.

Always passes — this is a bias, not a gate, per Table 48's own
"biases... ranking" language (as opposed to "removed from
candidates," the gate language `ContraindicatedExerciseRule` and
`EquipmentRule` implement).
"""

from __future__ import annotations

from app.domain.exercise.enums import MovementPattern
from app.domain.exercise.rules.context import ExerciseRecommendationRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_MINIMUM_ENTRIES = 4
_DEFAULT_IMBALANCE_RATIO = 1.5


class MovementBalanceRule(Rule[ExerciseRecommendationRuleContext]):
    """Attaches an ADVISORY recommendation when `PUSH`/`PULL`
    occurrences in `context.recent_movement_patterns` are imbalanced
    beyond `imbalance_ratio` and the candidate exercise is itself a
    `PUSH` or `PULL` movement — biasing away from the over-represented
    side and toward the under-represented one. Passes, with no
    recommendation, when fewer than `minimum_entries` patterns are
    supplied, when neither `PUSH` nor `PULL` appears in the recent
    history, when the candidate exercise is neither `PUSH` nor `PULL`,
    or when the two are already within `imbalance_ratio` of each
    other. Never fails.
    """

    def __init__(
        self,
        *,
        minimum_entries: int = _DEFAULT_MINIMUM_ENTRIES,
        imbalance_ratio: float = _DEFAULT_IMBALANCE_RATIO,
        severity: RecommendationSeverity = RecommendationSeverity.ADVISORY,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("exercise_recommendation.movement_balance"),
            name="Movement Balance",
            description="Biases exercise selection toward balanced push/pull training.",
            severity=severity,
        )
        self._minimum_entries = minimum_entries
        self._imbalance_ratio = imbalance_ratio

    def evaluate(self, context: ExerciseRecommendationRuleContext) -> RuleResult:
        patterns = context.recent_movement_patterns
        if len(patterns) < self._minimum_entries:
            return self._pass(
                f"Only {len(patterns)} recent movement pattern(s) supplied; at least "
                f"{self._minimum_entries} are needed to evaluate push/pull balance."
            )

        push_count = sum(1 for pattern in patterns if pattern is MovementPattern.PUSH)
        pull_count = sum(1 for pattern in patterns if pattern is MovementPattern.PULL)
        if push_count == 0 and pull_count == 0:
            return self._pass(
                "No push or pull movement pattern occurrences in the recent history; "
                "cannot evaluate push/pull balance."
            )

        candidate_pattern = context.exercise.movement_pattern
        if candidate_pattern not in (MovementPattern.PUSH, MovementPattern.PULL):
            return self._pass(
                "Candidate exercise is not a push or pull movement; push/pull balance does "
                "not apply."
            )

        over_represented = self._over_represented_side(push_count, pull_count)
        if over_represented is None:
            return self._pass(
                f"Push ({push_count}) and pull ({pull_count}) occurrences are within the "
                f"{self._imbalance_ratio:.2f}x balance range."
            )

        if candidate_pattern is over_represented:
            under_represented = self._other_pattern(over_represented)
            return self._pass(
                f"Recent training is biased toward {over_represented.value} "
                f"({push_count} push, {pull_count} pull).",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message=f"Recent training is {over_represented.value}-biased — "
                        f"consider a {under_represented.value} exercise instead.",
                    ),
                ),
            )

        return self._pass(
            f"This {candidate_pattern.value} exercise helps balance a "
            f"{over_represented.value}-biased recent history "
            f"({push_count} push, {pull_count} pull).",
            recommendations=(
                Recommendation(
                    severity=self.severity,
                    message=f"This {candidate_pattern.value} exercise helps balance recent "
                    f"{over_represented.value}-biased training.",
                ),
            ),
        )

    def _over_represented_side(self, push_count: int, pull_count: int) -> MovementPattern | None:
        if pull_count == 0 or push_count / pull_count > self._imbalance_ratio:
            return MovementPattern.PUSH if push_count > 0 else None
        if push_count == 0 or pull_count / push_count > self._imbalance_ratio:
            return MovementPattern.PULL if pull_count > 0 else None
        return None

    @staticmethod
    def _other_pattern(pattern: MovementPattern) -> MovementPattern:
        return MovementPattern.PULL if pattern is MovementPattern.PUSH else MovementPattern.PUSH
