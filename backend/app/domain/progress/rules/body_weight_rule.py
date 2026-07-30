"""`BodyWeightRule`: evaluates whether logged body weight is trending
toward the active goal's target weight.

Reuses the "Active goals only" guard
`docs/adr/0016-goal-alignment-combines-whole-snapshots.md` established
for `app.domain.goal.rules.body_weight_rule.BodyWeightRule` — a
same-named, deliberately independent sibling rule in a different engine,
the same "two engines legitimately re-evaluating related data for
different purposes" posture
`docs/adr/0018-safety-rule-engine-composition-and-authority.md`
documents for `SorenessRule`/`WorkloadRule`. That rule asks "is current
weight close to target, right now" (a snapshot comparison); this rule
asks "is weight moving closer to target over the evaluated history" (a
trend comparison) — genuinely different questions the same field can
answer.

Same documented unit-mismatch limitation as Goal Alignment's
`BodyWeightRule`: `Goal.target_weight` carries no `MeasurementUnit` of
its own, while `Progress.body_weight` is always paired with one on the
same record. This rule does not attempt unit conversion; see ADR 0016
for the full reasoning, unchanged here.
"""

from __future__ import annotations

from app.domain.goal.enums import GoalStatus
from app.domain.progress.rules.context import ProgressEvaluationRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_MINIMUM_ENTRIES = 2
_DEFAULT_WEIGHT_TOLERANCE = 2.0


class BodyWeightRule(Rule[ProgressEvaluationRuleContext]):
    """Triggers when at least `minimum_entries` (2 by default)
    body-weight-bearing progress entries exist, the gap between the most
    recent entry's `body_weight` and the goal's `target_weight` is
    outside `weight_tolerance` (2.0 by default), and that gap has not
    narrowed since the earliest such entry. Passes when there is no
    active goal, the goal has no `target_weight`, fewer than
    `minimum_entries` entries record `body_weight`, the latest entry is
    already within tolerance, or the gap has narrowed since the earliest
    entry (progress is being made, even if not yet at target)."""

    def __init__(
        self,
        *,
        minimum_entries: int = _DEFAULT_MINIMUM_ENTRIES,
        weight_tolerance: float = _DEFAULT_WEIGHT_TOLERANCE,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("progress_evaluation.body_weight"),
            name="Body Weight Trend",
            description="Evaluates whether body weight is trending toward the active goal.",
            severity=severity,
        )
        self._minimum_entries = minimum_entries
        self._weight_tolerance = weight_tolerance

    def evaluate(self, context: ProgressEvaluationRuleContext) -> RuleResult:
        goal = context.goal
        if goal is None:
            return self._pass("No active goal supplied; cannot evaluate body weight trend.")
        if goal.status is not GoalStatus.ACTIVE:
            return self._pass(f"Goal is not active (status: {goal.status.value}).")
        if goal.target_weight is None:
            return self._pass("Goal has no target weight to evaluate against.")

        weights = [
            entry.body_weight.value
            for entry in context.progress_history
            if entry.body_weight is not None
        ]
        if len(weights) < self._minimum_entries:
            return self._pass(
                f"Only {len(weights)} body weight entr(y/ies) available; at least "
                f"{self._minimum_entries} are needed to evaluate a trend."
            )

        target = goal.target_weight.value
        first_gap = abs(weights[0] - target)
        last_gap = abs(weights[-1] - target)

        if last_gap <= self._weight_tolerance:
            return self._pass(
                f"Latest body weight is within {self._weight_tolerance} of the target weight."
            )

        if last_gap < first_gap:
            return self._pass(
                f"Body weight is trending toward the target — gap narrowed from "
                f"{first_gap:.1f} to {last_gap:.1f}."
            )

        return self._fail(
            f"Body weight is not trending toward the target — gap did not narrow "
            f"({first_gap:.1f} to {last_gap:.1f}).",
            recommendations=(
                Recommendation(
                    severity=self.severity,
                    message="Body weight trend is not moving toward the goal — review nutrition "
                    "and training consistency.",
                ),
            ),
        )
