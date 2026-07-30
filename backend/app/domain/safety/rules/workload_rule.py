"""`WorkloadRule`: identifies an excessive recent workload spike — the
classic "too much, too soon" injury-risk pattern sports science
associates with a sudden jump in training volume relative to a recent
baseline.

Deliberately a different question from
`app.domain.workout.rules.deload_rule.DeloadRule`, not a duplicate of
it: `DeloadRule` flags *sustained* high volume with no lighter session
(a training-quality/performance concern, ADVISORY severity, owned by the
Progressive Overload engine). This rule flags a *sudden increase*
relative to a recent baseline — a spike, not a plateau — which is the
injury-risk pattern (loosely related to the sports-science
"acute:chronic workload ratio" concept, though this rule computes a
simpler two-window average ratio, not a true exponentially-weighted
ACWR — a stated simplification, not a claim of clinical rigor) a Safety
engine specifically cares about. Both rules may legitimately read the
same `WorkoutSessionSummary.total_volume` data and reach independent
conclusions — see `docs/adr/0018-safety-rule-engine-composition-and-authority.md`.
"""

from __future__ import annotations

from statistics import mean

from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity
from app.domain.safety.rules.context import SafetyRuleContext

_DEFAULT_RECENT_SESSIONS = 2
_DEFAULT_BASELINE_SESSIONS = 6
_DEFAULT_SPIKE_RATIO_THRESHOLD = 1.5


class WorkloadRule(Rule[SafetyRuleContext]):
    """Triggers when the average `total_volume` of the most recent
    `recent_sessions` (2 by default) is at least `spike_ratio_threshold`
    times (1.5x by default) the average `total_volume` of the
    `baseline_sessions` (6 by default) immediately preceding them.
    Passes when `context.recent_training` is `None`, when fewer than
    `recent_sessions + baseline_sessions` sessions are available, or
    when the baseline average is zero (no meaningful baseline)."""

    def __init__(
        self,
        *,
        recent_sessions: int = _DEFAULT_RECENT_SESSIONS,
        baseline_sessions: int = _DEFAULT_BASELINE_SESSIONS,
        spike_ratio_threshold: float = _DEFAULT_SPIKE_RATIO_THRESHOLD,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("safety.workload"),
            name="Workload Safety",
            description="Identifies a sudden training volume spike relative to a recent baseline.",
            severity=severity,
        )
        self._recent_sessions = recent_sessions
        self._baseline_sessions = baseline_sessions
        self._spike_ratio_threshold = spike_ratio_threshold

    def evaluate(self, context: SafetyRuleContext) -> RuleResult:
        recent_training = context.recent_training
        if recent_training is None:
            return self._pass(
                "No recent training history supplied; cannot evaluate workload safety."
            )

        sessions = recent_training.sessions
        required = self._recent_sessions + self._baseline_sessions
        if len(sessions) < required:
            return self._pass(
                f"Only {len(sessions)} session(s) available; at least {required} are needed "
                "to evaluate a workload spike."
            )

        recent = sessions[-self._recent_sessions :]
        baseline = sessions[-required : -self._recent_sessions]

        baseline_average = mean(session.total_volume for session in baseline)
        if baseline_average == 0:
            return self._pass("Baseline training volume is zero; no baseline to compare against.")

        recent_average = mean(session.total_volume for session in recent)
        ratio = recent_average / baseline_average

        if ratio >= self._spike_ratio_threshold:
            return self._fail(
                f"Recent average training volume of {recent_average:.0f} is {ratio:.1f}x the "
                f"baseline average of {baseline_average:.0f}, at or above the "
                f"{self._spike_ratio_threshold:.1f}x spike threshold.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Training volume has spiked sharply — ramp back up more "
                        "gradually to reduce injury risk.",
                    ),
                ),
            )

        return self._pass(
            f"Recent average training volume of {recent_average:.0f} is {ratio:.1f}x the "
            f"baseline average of {baseline_average:.0f}, within the "
            f"{self._spike_ratio_threshold:.1f}x spike threshold."
        )
