"""`TargetDateRule`: flags an Active goal whose `target_date` is
approaching soon or has already passed.
"""

from __future__ import annotations

from datetime import timedelta

from app.domain.goal.enums import GoalStatus
from app.domain.goal.rules.context import GoalAlignmentRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_APPROACHING_WITHIN_DAYS = 14


class TargetDateRule(Rule[GoalAlignmentRuleContext]):
    """Triggers when `context.goal.target_date` is within
    `approaching_within_days` of `context.reference_date` (not yet
    passed) or has already passed. Only evaluates goals with
    `status is GoalStatus.ACTIVE` — a goal that is Completed, Cancelled,
    or Expired has nothing left to be "approaching" or "overdue" toward;
    every rule in this package applies this same Active-only guard (see
    `docs/adr/0016-goal-alignment-combines-whole-snapshots.md`). Passes,
    with no recommendation, for a non-Active goal or when the target date
    is comfortably in the future.
    """

    def __init__(
        self,
        *,
        approaching_within_days: int = _DEFAULT_APPROACHING_WITHIN_DAYS,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("goal_alignment.target_date"),
            name="Target Date",
            description="Flags a goal whose target date is approaching or overdue.",
            severity=severity,
        )
        self._approaching_within = timedelta(days=approaching_within_days)

    def evaluate(self, context: GoalAlignmentRuleContext) -> RuleResult:
        goal = context.goal
        if goal.status is not GoalStatus.ACTIVE:
            return self._pass(f"Goal is not active (status: {goal.status.value}).")

        days_remaining = (goal.target_date.value - context.reference_date).days

        if days_remaining < 0:
            return self._fail(
                f"Target date {goal.target_date.value.isoformat()} is "
                f"{abs(days_remaining)} day(s) overdue.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="This goal's target date has passed — consider updating "
                        "the target date or reviewing progress toward it.",
                    ),
                ),
            )

        if timedelta(days=days_remaining) <= self._approaching_within:
            return self._fail(
                f"Target date {goal.target_date.value.isoformat()} is "
                f"{days_remaining} day(s) away.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="This goal's target date is approaching soon — review "
                        "whether current progress is on track.",
                    ),
                ),
            )

        return self._pass(
            f"Target date {goal.target_date.value.isoformat()} is "
            f"{days_remaining} day(s) away, beyond the "
            f"{self._approaching_within.days}-day approaching window."
        )
