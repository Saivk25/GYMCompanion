"""`StrengthGoalRule`: checks whether enough strength progress
information exists to assess an Active goal's `target_strength`.

Always passes, by explicit design (this phase's own instruction: "if
insufficient data exists, return a passing RuleResult with an explanation
rather than failing"). `GoalAlignmentRuleContext` carries only `Goal` and
`Progress` snapshots — neither tracks strength/lift performance
(`WorkoutSession`/`ExercisePerformance` data, which this phase's Do Not
list excludes: "no progressive overload," "no training load"). Sufficient
strength data can therefore never actually exist within this context in
this phase; this rule exists as an honest, forward-looking acknowledgment
of that gap, not a dead check waiting to someday find data. See
`docs/adr/0016-goal-alignment-combines-whole-snapshots.md`.
"""

from __future__ import annotations

from app.domain.goal.enums import GoalStatus
from app.domain.goal.rules.context import GoalAlignmentRuleContext
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity


class StrengthGoalRule(Rule[GoalAlignmentRuleContext]):
    """Always passes. Distinguishes, in its explanation only, between "no
    strength target set" and "a strength target exists but no strength
    progress data is available to assess it" — useful context for a
    caller even though neither case ever triggers a finding.
    """

    def __init__(
        self,
        *,
        severity: RecommendationSeverity = RecommendationSeverity.INFO,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("goal_alignment.strength_goal"),
            name="Strength Goal",
            description=(
                "Checks whether sufficient strength progress data exists to assess the goal."
            ),
            severity=severity,
        )

    def evaluate(self, context: GoalAlignmentRuleContext) -> RuleResult:
        goal = context.goal
        if goal.status is not GoalStatus.ACTIVE:
            return self._pass(f"Goal is not active (status: {goal.status.value}).")

        if goal.target_strength is None:
            return self._pass("Goal has no strength target to assess.")

        return self._pass(
            "Goal has a strength target, but no strength progress data is available in "
            "this context to assess it."
        )
