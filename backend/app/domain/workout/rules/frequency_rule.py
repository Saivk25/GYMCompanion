"""`FrequencyRule`: flags a training frequency below a configured minimum
sessions-per-week rate, computed purely from the span between the
earliest and latest session in the evaluated history — no wall-clock
read, no external "today" (see `context.py`'s module docstring for why
this package needs no `reference_date` field the way
`GoalAlignmentRuleContext` did).
"""

from __future__ import annotations

from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity
from app.domain.workout.rules.context import ProgressiveOverloadRuleContext

_DEFAULT_MINIMUM_SESSIONS = 2
_DEFAULT_MINIMUM_SESSIONS_PER_WEEK = 2.0
_DAYS_PER_WEEK = 7


class FrequencyRule(Rule[ProgressiveOverloadRuleContext]):
    """Triggers when the evaluated session history's rate of sessions per
    week — `len(sessions) / (span in days / 7)`, spanning from the
    earliest to the latest session date — falls below
    `minimum_sessions_per_week` (2.0 by default). Passes when fewer than
    `minimum_sessions` sessions are available, or when every session
    shares the same date (a zero-day span cannot produce a rate)."""

    def __init__(
        self,
        *,
        minimum_sessions: int = _DEFAULT_MINIMUM_SESSIONS,
        minimum_sessions_per_week: float = _DEFAULT_MINIMUM_SESSIONS_PER_WEEK,
        severity: RecommendationSeverity = RecommendationSeverity.ADVISORY,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("progressive_overload.frequency"),
            name="Frequency",
            description="Flags a training frequency below the configured minimum.",
            severity=severity,
        )
        self._minimum_sessions = minimum_sessions
        self._minimum_sessions_per_week = minimum_sessions_per_week

    def evaluate(self, context: ProgressiveOverloadRuleContext) -> RuleResult:
        sessions = context.sessions
        if len(sessions) < self._minimum_sessions:
            return self._pass(
                f"Only {len(sessions)} session(s) available; at least "
                f"{self._minimum_sessions} are needed to evaluate training frequency."
            )

        span_days = (sessions[-1].session_date.value - sessions[0].session_date.value).days
        if span_days <= 0:
            return self._pass(
                "All evaluated sessions fall on the same date; cannot compute a weekly rate."
            )

        sessions_per_week = len(sessions) / (span_days / _DAYS_PER_WEEK)
        if sessions_per_week < self._minimum_sessions_per_week:
            return self._fail(
                f"Training frequency of {sessions_per_week:.1f} sessions/week is below the "
                f"minimum of {self._minimum_sessions_per_week:.1f}.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Training frequency has dropped — consider scheduling sessions "
                        "more consistently.",
                    ),
                ),
            )

        return self._pass(
            f"Training frequency of {sessions_per_week:.1f} sessions/week meets the minimum "
            f"of {self._minimum_sessions_per_week:.1f}."
        )
