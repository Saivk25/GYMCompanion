"""`ConsistencyRule`: determines whether sufficient progress entries exist
for meaningful evaluation — this codebase's implementation of the Domain
Model & Decision Engine Bible's own "Minimum evidence rule" (Table 54:
"A Trend has fewer than the minimum data points... UI must show 'not
enough data yet' instead of a line").

**Deliberately fails, rather than passes, on insufficient data — the one
rule in this package (and the first in this codebase's Progress-adjacent
engines) that departs from the "missing data passes" default.** This
phase's own task states that default applies "unless the Product Bible
explicitly specifies otherwise," and the Bible does: the Minimum evidence
rule's whole point is to flag insufficient logging as something to
surface, not something to silently tolerate. Every other rule in this
package still follows the default (a missing goal, a missing target, an
individual measurement never logged — none of those are failures); only
"not enough entries exist at all, or logging has gone stale" is treated
as a real, actionable finding here. See
`docs/adr/0019-progress-evaluation-consistency-and-plateau-scope.md`.

The only rule in this package that reads `context.reference_date` — the
recency check ("is the latest entry recent enough relative to now")
inherently needs an external "now" a bounded history alone cannot
supply, unlike every other rule here.
"""

from __future__ import annotations

from app.domain.progress.rules.context import ProgressEvaluationRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_MINIMUM_ENTRIES = 3
_DEFAULT_MAXIMUM_DAYS_SINCE_LAST_ENTRY = 14


class ConsistencyRule(Rule[ProgressEvaluationRuleContext]):
    """Triggers when `context.progress_history` has fewer than
    `minimum_entries` (3 by default) entries, or when the most recent
    entry's `progress_date` is more than `maximum_days_since_last_entry`
    (14 by default) days before `context.reference_date`. Passes only
    when both conditions are satisfied."""

    def __init__(
        self,
        *,
        minimum_entries: int = _DEFAULT_MINIMUM_ENTRIES,
        maximum_days_since_last_entry: int = _DEFAULT_MAXIMUM_DAYS_SINCE_LAST_ENTRY,
        severity: RecommendationSeverity = RecommendationSeverity.ADVISORY,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("progress_evaluation.consistency"),
            name="Consistency",
            description=(
                "Determines whether enough progress entries exist for meaningful evaluation."
            ),
            severity=severity,
        )
        self._minimum_entries = minimum_entries
        self._maximum_days_since_last_entry = maximum_days_since_last_entry

    def evaluate(self, context: ProgressEvaluationRuleContext) -> RuleResult:
        history = context.progress_history

        if len(history) < self._minimum_entries:
            return self._fail(
                f"Only {len(history)} progress entr(y/ies) recorded; at least "
                f"{self._minimum_entries} are needed for meaningful evaluation.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Log progress more regularly to enable meaningful trend "
                        "evaluation.",
                    ),
                ),
            )

        days_since_last_entry = (context.reference_date - history[-1].progress_date.value).days
        if days_since_last_entry > self._maximum_days_since_last_entry:
            return self._fail(
                f"The most recent progress entry is {days_since_last_entry} day(s) old, "
                f"beyond the {self._maximum_days_since_last_entry}-day freshness window.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Progress logging has gone stale — log a new entry to keep "
                        "evaluation meaningful.",
                    ),
                ),
            )

        return self._pass(
            f"{len(history)} progress entries recorded, most recently "
            f"{days_since_last_entry} day(s) ago — sufficient for meaningful evaluation."
        )
