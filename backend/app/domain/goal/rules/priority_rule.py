"""`PriorityRule`: highlights an Active goal whose priority is high
enough to warrant attention.

Not a problem check like this package's other rules — a high-priority
goal is not something wrong, it is something to keep in focus. Triggers
(via `_fail()`, the same "did this rule surface a finding" mechanism
every other rule uses) with a gentle default severity (`ADVISORY`, not
`WARNING`) to reflect that difference in kind — see
`docs/adr/0016-goal-alignment-combines-whole-snapshots.md`.
"""

from __future__ import annotations

from app.domain.goal.enums import GoalStatus
from app.domain.goal.rules.context import GoalAlignmentRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_MAXIMUM_PRIORITY_TO_HIGHLIGHT = 2


class PriorityRule(Rule[GoalAlignmentRuleContext]):
    """Triggers when `context.goal.priority` is set and at or above the
    urgency implied by `maximum_priority_to_highlight` (2 by default — on
    `Priority`'s own 1-5 scale, where 1 is highest, this catches
    priorities 1 and 2). Only evaluates Active goals; passes, with no
    recommendation, for a non-Active goal, a goal with no priority set, or
    a priority below the highlighted range.
    """

    def __init__(
        self,
        *,
        maximum_priority_to_highlight: int = _DEFAULT_MAXIMUM_PRIORITY_TO_HIGHLIGHT,
        severity: RecommendationSeverity = RecommendationSeverity.ADVISORY,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("goal_alignment.priority"),
            name="Priority",
            description="Highlights high-priority active goals that may require attention.",
            severity=severity,
        )
        self._maximum_priority_to_highlight = maximum_priority_to_highlight

    def evaluate(self, context: GoalAlignmentRuleContext) -> RuleResult:
        goal = context.goal
        if goal.status is not GoalStatus.ACTIVE:
            return self._pass(f"Goal is not active (status: {goal.status.value}).")

        if goal.priority is None:
            return self._pass("Goal has no priority set.")

        if goal.priority.value <= self._maximum_priority_to_highlight:
            return self._fail(
                f"Goal priority {goal.priority.value} is within the "
                f"top {self._maximum_priority_to_highlight} and may need attention.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="This is a high-priority goal — keep it in focus.",
                    ),
                ),
            )

        return self._pass(
            f"Goal priority {goal.priority.value} is below the highlighted "
            f"top {self._maximum_priority_to_highlight}."
        )
