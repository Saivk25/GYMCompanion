"""`DeloadRule`: identifies a sustained-overload pattern — a trailing run
of sessions that has stayed persistently near the historical peak volume
with no lighter session mixed in — and suggests a deload.

Not the same "deload trigger" the Domain Model & Decision Engine Bible
names under Recovery Rules (Section 10.3, "Governs the RecoveryState
computation and deload triggering") — that trigger reads `RecoveryState`
and `ReadinessCheckIn` data (`RecoveryState`/`Recovery Rule Engine` are
both explicitly out of scope for this phase). This rule is a narrower,
workout-volume-only heuristic that belongs to Section 10.1's Workout
Rules ("Governs plan generation, volume, and substitution"): it can only
see that training volume has stayed high without a break, never whether
the user is actually fatigued or under-recovered. See
`docs/adr/0017-progressive-overload-session-level-trends.md` for the
full reasoning on why these are two distinct, non-overlapping deload
signals.
"""

from __future__ import annotations

from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity
from app.domain.workout.rules.context import ProgressiveOverloadRuleContext

_DEFAULT_LOOKBACK_SESSIONS = 6
_DEFAULT_HIGH_VOLUME_RATIO = 0.90


class DeloadRule(Rule[ProgressiveOverloadRuleContext]):
    """Triggers when every one of the trailing `lookback_sessions`
    sessions (6 by default) has a `total_volume` at or above
    `high_volume_ratio` (90% by default) of the peak `total_volume` seen
    across the whole evaluated history — a run with no lighter session to
    let fatigue dissipate. Passes when fewer than `lookback_sessions`
    sessions are available, or when the historical peak volume is zero."""

    def __init__(
        self,
        *,
        lookback_sessions: int = _DEFAULT_LOOKBACK_SESSIONS,
        high_volume_ratio: float = _DEFAULT_HIGH_VOLUME_RATIO,
        severity: RecommendationSeverity = RecommendationSeverity.ADVISORY,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("progressive_overload.deload"),
            name="Deload",
            description="Identifies a sustained high-volume pattern that suggests a deload.",
            severity=severity,
        )
        self._lookback_sessions = lookback_sessions
        self._high_volume_ratio = high_volume_ratio

    def evaluate(self, context: ProgressiveOverloadRuleContext) -> RuleResult:
        sessions = context.sessions
        if len(sessions) < self._lookback_sessions:
            return self._pass(
                f"Only {len(sessions)} session(s) available; at least "
                f"{self._lookback_sessions} are needed to assess a sustained overload pattern."
            )

        peak_volume = max(session.total_volume for session in sessions)
        if peak_volume == 0:
            return self._pass("No training volume recorded; nothing to assess for overload.")

        recent = sessions[-self._lookback_sessions :]
        threshold = self._high_volume_ratio * peak_volume
        sustained_high = all(session.total_volume >= threshold for session in recent)

        if sustained_high:
            return self._fail(
                f"The last {self._lookback_sessions} sessions have all stayed at or above "
                f"{self._high_volume_ratio:.0%} of peak training volume with no lighter "
                "session in between.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Sustained high training volume with no letup — consider "
                        "scheduling a deload week.",
                    ),
                ),
            )

        return self._pass(
            f"Training volume shows normal variation across the last {self._lookback_sessions} "
            "sessions; no sustained overload pattern detected."
        )
