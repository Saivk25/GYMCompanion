"""`BodyFatRule`: compares a Progress snapshot's current body fat
percentage against an Active goal's target body fat percentage, when
both are available.

Unlike `body_weight_rule.py`, no unit-reconciliation caveat applies here:
both `Goal.target_body_fat`
(`app.domain.goal.value_objects.TargetBodyFat`) and
`Progress.body_fat_percentage`
(`app.domain.progress.value_objects.BodyFatPercentage`) are defined as
the same thing — a 0-100 percentage — so comparing their raw values is
directly meaningful, not an assumption this rule has to state as a
limitation.
"""

from __future__ import annotations

from app.domain.goal.enums import GoalStatus
from app.domain.goal.rules.context import GoalAlignmentRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_BODY_FAT_TOLERANCE = 3.0


class BodyFatRule(Rule[GoalAlignmentRuleContext]):
    """Triggers when `context.progress.body_fat_percentage` differs from
    `context.goal.target_body_fat` by more than `body_fat_tolerance`
    (3.0 percentage points by default). Only evaluates Active goals with
    both a target body fat and a progress snapshot carrying a body fat
    percentage; passes, with an explanation, whenever any of those is
    missing.
    """

    def __init__(
        self,
        *,
        body_fat_tolerance: float = _DEFAULT_BODY_FAT_TOLERANCE,
        severity: RecommendationSeverity = RecommendationSeverity.ADVISORY,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("goal_alignment.body_fat"),
            name="Body Fat",
            description="Compares current body fat percentage with the goal's target.",
            severity=severity,
        )
        self._body_fat_tolerance = body_fat_tolerance

    def evaluate(self, context: GoalAlignmentRuleContext) -> RuleResult:
        goal = context.goal
        if goal.status is not GoalStatus.ACTIVE:
            return self._pass(f"Goal is not active (status: {goal.status.value}).")

        if goal.target_body_fat is None:
            return self._pass("Goal has no target body fat to compare against.")

        if context.progress is None or context.progress.body_fat_percentage is None:
            return self._pass(
                "No recent body fat percentage recorded to compare against the target."
            )

        current = context.progress.body_fat_percentage.value
        target = goal.target_body_fat.value
        difference = abs(current - target)

        if difference > self._body_fat_tolerance:
            return self._fail(
                f"Current body fat of {current:.1f}% differs from the target of "
                f"{target:.1f}% by {difference:.1f} points, beyond the "
                f"{self._body_fat_tolerance:.1f}-point tolerance.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Current body fat is not yet within range of this goal's target.",
                    ),
                ),
            )

        return self._pass(
            f"Current body fat of {current:.1f}% is within {self._body_fat_tolerance:.1f} "
            f"points of the target of {target:.1f}%."
        )
