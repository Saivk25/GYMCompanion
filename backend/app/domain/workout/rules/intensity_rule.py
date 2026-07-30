"""`IntensityRule`: flags a declining load/intensity trend across a
history of `WorkoutSessionSummary` values.

"Intensity" here is average load — the mean `SetWeight` across every
logged set in a session (`WorkoutSessionSummary.average_load`), not a
%1RM-normalized measure (this phase estimates no 1RM; see
`WorkoutSessionSummary`'s own docstring for the stated whole-session,
mixed-exercise, bodyweight-blending simplifications this metric carries).
"""

from __future__ import annotations

from statistics import mean

from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity
from app.domain.workout.rules.context import ProgressiveOverloadRuleContext, WorkoutSessionSummary

_DEFAULT_MINIMUM_SESSIONS = 4
_DEFAULT_DECLINE_THRESHOLD = 0.15


def _earlier_and_later_halves(
    sessions: tuple[WorkoutSessionSummary, ...],
) -> tuple[tuple[WorkoutSessionSummary, ...], tuple[WorkoutSessionSummary, ...]]:
    """Splits a chronologically-ordered session history into an earlier
    baseline half and a later comparison half. Duplicated verbatim from
    `volume_rule.py` rather than shared — see
    `docs/adr/0017-progressive-overload-session-level-trends.md` for why
    this package keeps each rule independent rather than introducing a
    shared helper module between them, the same "small duplication over
    coupling" posture `docs/adr/0014-readiness-rule-composition.md`
    already established."""
    midpoint = len(sessions) // 2
    return sessions[:midpoint], sessions[midpoint:]


class IntensityRule(Rule[ProgressiveOverloadRuleContext]):
    """Triggers when the average `average_load` of the later half of the
    evaluated session history has declined by more than
    `decline_threshold` relative to the earlier half's average (15% by
    default). Passes when fewer than `minimum_sessions` sessions are
    available, when the earlier half's average load is zero, or when
    neither half has any session with recorded load data (e.g. an
    entirely bodyweight session history)."""

    def __init__(
        self,
        *,
        minimum_sessions: int = _DEFAULT_MINIMUM_SESSIONS,
        decline_threshold: float = _DEFAULT_DECLINE_THRESHOLD,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("progressive_overload.intensity"),
            name="Intensity",
            description="Flags a declining load/intensity trend across a session history.",
            severity=severity,
        )
        self._minimum_sessions = minimum_sessions
        self._decline_threshold = decline_threshold

    def evaluate(self, context: ProgressiveOverloadRuleContext) -> RuleResult:
        sessions = context.sessions
        if len(sessions) < self._minimum_sessions:
            return self._pass(
                f"Only {len(sessions)} session(s) available; at least "
                f"{self._minimum_sessions} are needed to evaluate an intensity trend."
            )

        earlier, later = _earlier_and_later_halves(sessions)
        earlier_loads = [
            session.average_load for session in earlier if session.average_load is not None
        ]
        later_loads = [
            session.average_load for session in later if session.average_load is not None
        ]

        if not earlier_loads or not later_loads:
            return self._pass("No recorded load data in one or both halves of the session history.")

        earlier_average = mean(earlier_loads)
        later_average = mean(later_loads)

        if earlier_average == 0:
            return self._pass(
                "Earlier sessions recorded no load; no baseline to compare intensity against."
            )

        relative_change = (later_average - earlier_average) / earlier_average
        if relative_change <= -self._decline_threshold:
            return self._fail(
                f"Average load declined from {earlier_average:.1f} to {later_average:.1f} "
                f"per session ({relative_change:.0%}), exceeding the "
                f"{self._decline_threshold:.0%} decline threshold.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Load is trending down — consider whether this is a planned "
                        "deload or an unplanned drop in intensity.",
                    ),
                ),
            )

        return self._pass(
            f"Average load changed by {relative_change:+.0%} from {earlier_average:.1f} to "
            f"{later_average:.1f} per session, within the {self._decline_threshold:.0%} "
            f"decline threshold."
        )
