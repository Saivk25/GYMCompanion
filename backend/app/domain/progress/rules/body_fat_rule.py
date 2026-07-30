"""`BodyFatRule`: evaluates whether logged body fat percentage is trending
toward the active goal's target body fat.

Same "trend, not snapshot" distinction `body_weight_rule.py`'s module
docstring documents relative to
`app.domain.goal.rules.body_fat_rule.BodyFatRule`. No unit-mismatch
caveat is needed here (unlike `BodyWeightRule`): both `TargetBodyFat` and
`BodyFatPercentage` are unambiguously 0-100 percentages.
"""

from __future__ import annotations

from app.domain.goal.enums import GoalStatus
from app.domain.progress.rules.context import ProgressEvaluationRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_MINIMUM_ENTRIES = 2
_DEFAULT_BODY_FAT_TOLERANCE = 3.0


class BodyFatRule(Rule[ProgressEvaluationRuleContext]):
    """Triggers when at least `minimum_entries` (2 by default)
    body-fat-bearing progress entries exist, the gap between the most
    recent entry's `body_fat_percentage` and the goal's `target_body_fat`
    is outside `body_fat_tolerance` (3.0 by default), and that gap has
    not narrowed since the earliest such entry. Passes when there is no
    active goal, the goal has no `target_body_fat`, fewer than
    `minimum_entries` entries record `body_fat_percentage`, the latest
    entry is already within tolerance, or the gap has narrowed since the
    earliest entry."""

    def __init__(
        self,
        *,
        minimum_entries: int = _DEFAULT_MINIMUM_ENTRIES,
        body_fat_tolerance: float = _DEFAULT_BODY_FAT_TOLERANCE,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("progress_evaluation.body_fat"),
            name="Body Fat Trend",
            description="Evaluates whether body fat percentage is trending toward the active goal.",
            severity=severity,
        )
        self._minimum_entries = minimum_entries
        self._body_fat_tolerance = body_fat_tolerance

    def evaluate(self, context: ProgressEvaluationRuleContext) -> RuleResult:
        goal = context.goal
        if goal is None:
            return self._pass("No active goal supplied; cannot evaluate body fat trend.")
        if goal.status is not GoalStatus.ACTIVE:
            return self._pass(f"Goal is not active (status: {goal.status.value}).")
        if goal.target_body_fat is None:
            return self._pass("Goal has no target body fat to evaluate against.")

        percentages = [
            entry.body_fat_percentage.value
            for entry in context.progress_history
            if entry.body_fat_percentage is not None
        ]
        if len(percentages) < self._minimum_entries:
            return self._pass(
                f"Only {len(percentages)} body fat entr(y/ies) available; at least "
                f"{self._minimum_entries} are needed to evaluate a trend."
            )

        target = goal.target_body_fat.value
        first_gap = abs(percentages[0] - target)
        last_gap = abs(percentages[-1] - target)

        if last_gap <= self._body_fat_tolerance:
            return self._pass(
                f"Latest body fat percentage is within {self._body_fat_tolerance} of the "
                "target body fat."
            )

        if last_gap < first_gap:
            return self._pass(
                f"Body fat percentage is trending toward the target — gap narrowed from "
                f"{first_gap:.1f} to {last_gap:.1f}."
            )

        return self._fail(
            f"Body fat percentage is not trending toward the target — gap did not narrow "
            f"({first_gap:.1f} to {last_gap:.1f}).",
            recommendations=(
                Recommendation(
                    severity=self.severity,
                    message="Body fat trend is not moving toward the goal — review nutrition "
                    "and training consistency.",
                ),
            ),
        )
