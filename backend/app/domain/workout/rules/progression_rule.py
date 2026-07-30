"""`ProgressionRule`: detects a lack of progression — no meaningful new
peak in either training volume or load — across a history of
`WorkoutSessionSummary` values.

Deliberately a different question from `VolumeRule`/`IntensityRule`: those
two ask "is the recent average trending down." This rule asks "has
*either* metric reached a genuinely new high at all" — a session history
can show no decline (passing both `VolumeRule` and `IntensityRule`) while
still plateauing at the same peak indefinitely, which is exactly the
"deterministic rep/load/set progression" gap Product Bible Section names
for the Progressive overload engine. Comparing peaks (not averages)
between the earlier and later halves is what distinguishes "plateaued at
the same ceiling" from "declined."
"""

from __future__ import annotations

from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity
from app.domain.workout.rules.context import ProgressiveOverloadRuleContext, WorkoutSessionSummary

_DEFAULT_MINIMUM_SESSIONS = 4
_DEFAULT_MINIMUM_GROWTH = 0.05


def _earlier_and_later_halves(
    sessions: tuple[WorkoutSessionSummary, ...],
) -> tuple[tuple[WorkoutSessionSummary, ...], tuple[WorkoutSessionSummary, ...]]:
    """Splits a chronologically-ordered session history into an earlier
    baseline half and a later comparison half. Duplicated verbatim from
    `volume_rule.py`/`intensity_rule.py` — see that module's docstring
    for why this package keeps each rule independent rather than sharing
    this helper."""
    midpoint = len(sessions) // 2
    return sessions[:midpoint], sessions[midpoint:]


def _relative_growth(earlier_peak: float, later_peak: float) -> float | None:
    if earlier_peak == 0:
        return None
    return (later_peak - earlier_peak) / earlier_peak


class ProgressionRule(Rule[ProgressiveOverloadRuleContext]):
    """Triggers when neither peak `total_volume` nor peak `average_load`
    grew by at least `minimum_growth` (5% by default) from the earlier
    half of the evaluated session history to the later half. Passes when
    fewer than `minimum_sessions` sessions are available, or when at
    least one of the two metrics shows the required growth."""

    def __init__(
        self,
        *,
        minimum_sessions: int = _DEFAULT_MINIMUM_SESSIONS,
        minimum_growth: float = _DEFAULT_MINIMUM_GROWTH,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("progressive_overload.progression"),
            name="Progression",
            description="Detects a lack of new peak volume or load across a session history.",
            severity=severity,
        )
        self._minimum_sessions = minimum_sessions
        self._minimum_growth = minimum_growth

    def evaluate(self, context: ProgressiveOverloadRuleContext) -> RuleResult:
        sessions = context.sessions
        if len(sessions) < self._minimum_sessions:
            return self._pass(
                f"Only {len(sessions)} session(s) available; at least "
                f"{self._minimum_sessions} are needed to evaluate progression."
            )

        earlier, later = _earlier_and_later_halves(sessions)

        volume_growth = _relative_growth(
            max(session.total_volume for session in earlier),
            max(session.total_volume for session in later),
        )

        earlier_loads = [
            session.average_load for session in earlier if session.average_load is not None
        ]
        later_loads = [
            session.average_load for session in later if session.average_load is not None
        ]
        load_growth = (
            _relative_growth(max(earlier_loads), max(later_loads))
            if earlier_loads and later_loads
            else None
        )

        progressed = (volume_growth is not None and volume_growth >= self._minimum_growth) or (
            load_growth is not None and load_growth >= self._minimum_growth
        )

        if not progressed:
            return self._fail(
                "No meaningful increase in peak volume or peak load was detected across the "
                f"evaluated sessions (minimum growth threshold: {self._minimum_growth:.0%}).",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Progress has plateaued — consider increasing load, reps, or "
                        "sets, or varying the program.",
                    ),
                ),
            )

        best_growth = max(g for g in (volume_growth, load_growth) if g is not None)
        return self._pass(
            f"Peak volume and/or load grew by at least {best_growth:.0%}, meeting the "
            f"{self._minimum_growth:.0%} minimum growth threshold."
        )
