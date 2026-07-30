"""`BodyWeightRule`: compares a Progress snapshot's current body weight
against an Active goal's target weight, when both are available.

Known limitation, stated here rather than silently assumed:
`Goal.target_weight` (`app.domain.goal.value_objects.TargetWeight`)
carries no unit of its own — its docstring already notes it is "in
whatever unit the caller has agreed with the user" — while
`Progress.body_weight` is always paired with a `MeasurementUnit`
(`app.domain.progress.enums`) on the same `Progress` record. This rule
does not reconcile the two: it compares the raw numeric values as given,
on the assumption a caller supplies both in the same unit. Real unit
reconciliation is out of scope for this phase — see
`docs/adr/0016-goal-alignment-combines-whole-snapshots.md`.
"""

from __future__ import annotations

from app.domain.goal.enums import GoalStatus
from app.domain.goal.rules.context import GoalAlignmentRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_WEIGHT_TOLERANCE = 2.0


class BodyWeightRule(Rule[GoalAlignmentRuleContext]):
    """Triggers when `context.progress.body_weight` differs from
    `context.goal.target_weight` by more than `weight_tolerance` (2.0 by
    default, in whatever unit both values happen to share — see this
    module's docstring). Only evaluates Active goals with both a target
    weight and a progress snapshot carrying a body weight; passes, with
    an explanation, whenever any of those is missing — "insufficient
    data" is a normal outcome here, not treated as a failure.
    """

    def __init__(
        self,
        *,
        weight_tolerance: float = _DEFAULT_WEIGHT_TOLERANCE,
        severity: RecommendationSeverity = RecommendationSeverity.ADVISORY,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("goal_alignment.body_weight"),
            name="Body Weight",
            description="Compares current body weight with the goal's target weight.",
            severity=severity,
        )
        self._weight_tolerance = weight_tolerance

    def evaluate(self, context: GoalAlignmentRuleContext) -> RuleResult:
        goal = context.goal
        if goal.status is not GoalStatus.ACTIVE:
            return self._pass(f"Goal is not active (status: {goal.status.value}).")

        if goal.target_weight is None:
            return self._pass("Goal has no target weight to compare against.")

        if context.progress is None or context.progress.body_weight is None:
            return self._pass("No recent body weight recorded to compare against the target.")

        current = context.progress.body_weight.value
        target = goal.target_weight.value
        difference = abs(current - target)

        if difference > self._weight_tolerance:
            return self._fail(
                f"Current body weight of {current:.1f} differs from the target of "
                f"{target:.1f} by {difference:.1f}, beyond the "
                f"{self._weight_tolerance:.1f} tolerance.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Current weight is not yet within range of this goal's target.",
                    ),
                ),
            )

        return self._pass(
            f"Current body weight of {current:.1f} is within {self._weight_tolerance:.1f} "
            f"of the target of {target:.1f}."
        )
