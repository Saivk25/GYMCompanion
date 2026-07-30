"""`VolumeRule`: flags a declining training volume trend across a
history of `WorkoutSessionSummary` values.

"Volume" here is volume load — sum(weight x reps) across every logged set
in a session (`WorkoutSessionSummary.total_volume`) — the standard
strength-training definition, and the same metric Product Bible Table 18
names as tracked ("Volume per muscle group... session duration") and
derives "progression rate; overtraining risk" from, at the coarser
whole-session granularity this phase implements (see
`docs/adr/0017-progressive-overload-session-level-trends.md`).
"""

from __future__ import annotations

from statistics import mean

from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity
from app.domain.workout.rules.context import ProgressiveOverloadRuleContext, WorkoutSessionSummary

_DEFAULT_MINIMUM_SESSIONS = 4
_DEFAULT_DECLINE_THRESHOLD = 0.20


def _earlier_and_later_halves(
    sessions: tuple[WorkoutSessionSummary, ...],
) -> tuple[tuple[WorkoutSessionSummary, ...], tuple[WorkoutSessionSummary, ...]]:
    """Splits a chronologically-ordered session history into an earlier
    baseline half and a later comparison half. An odd count gives the
    later half the extra session, weighting the comparison toward more
    recent data rather than less."""
    midpoint = len(sessions) // 2
    return sessions[:midpoint], sessions[midpoint:]


class VolumeRule(Rule[ProgressiveOverloadRuleContext]):
    """Triggers when the average `total_volume` of the later half of the
    evaluated session history has declined by more than
    `decline_threshold` relative to the earlier half's average (20% by
    default — this phase's own choice, not a Bible-mandated figure).
    Passes, with an explanation naming the reason, when fewer than
    `minimum_sessions` sessions are available, or when the earlier half's
    average volume is zero (no meaningful baseline to compare against).
    """

    def __init__(
        self,
        *,
        minimum_sessions: int = _DEFAULT_MINIMUM_SESSIONS,
        decline_threshold: float = _DEFAULT_DECLINE_THRESHOLD,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("progressive_overload.volume"),
            name="Volume",
            description="Flags a declining training volume trend across a session history.",
            severity=severity,
        )
        self._minimum_sessions = minimum_sessions
        self._decline_threshold = decline_threshold

    def evaluate(self, context: ProgressiveOverloadRuleContext) -> RuleResult:
        sessions = context.sessions
        if len(sessions) < self._minimum_sessions:
            return self._pass(
                f"Only {len(sessions)} session(s) available; at least "
                f"{self._minimum_sessions} are needed to evaluate a volume trend."
            )

        earlier, later = _earlier_and_later_halves(sessions)
        earlier_average = mean(session.total_volume for session in earlier)
        later_average = mean(session.total_volume for session in later)

        if earlier_average == 0:
            return self._pass(
                "Earlier sessions recorded no training volume; no baseline to compare against."
            )

        relative_change = (later_average - earlier_average) / earlier_average
        if relative_change <= -self._decline_threshold:
            return self._fail(
                f"Average training volume declined from {earlier_average:.0f} to "
                f"{later_average:.0f} per session ({relative_change:.0%}), exceeding the "
                f"{self._decline_threshold:.0%} decline threshold.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Training volume is trending down — review recent programming "
                        "or check for accumulated fatigue.",
                    ),
                ),
            )

        return self._pass(
            f"Average training volume changed by {relative_change:+.0%} from "
            f"{earlier_average:.0f} to {later_average:.0f} per session, within the "
            f"{self._decline_threshold:.0%} decline threshold."
        )
