"""`RecoveryRule`: flags an elevated resting heart rate or a depressed
heart rate variability — the two wearable-derived metrics
`app.domain.readiness.readiness.Readiness` carries beyond the Domain
Model & Decision Engine Bible's own self-reported `ReadinessCheckIn`
fields (see that aggregate's module docstring).

The one rule in this package that reads two context fields at once. They
are evaluated independently against fixed thresholds — not combined into
a single score, index, or weighted formula. That kind of combination
(and, more importantly, comparing today's reading against *this user's
own* rolling baseline rather than a fixed population threshold) is
exactly the "recovery score" / "fatigue score" work this phase's Do NOT
list excludes; see `docs/adr/0014-readiness-rule-composition.md`.
"""

from __future__ import annotations

from app.domain.readiness.rules.context import ReadinessRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_MAXIMUM_RESTING_HEART_RATE = 70.0
_DEFAULT_MINIMUM_HEART_RATE_VARIABILITY = 40.0


class RecoveryRule(Rule[ReadinessRuleContext]):
    """Triggers when `context.resting_heart_rate` is above
    `maximum_resting_heart_rate`, or `context.heart_rate_variability` is
    below `minimum_heart_rate_variability`, or both. Both thresholds are
    fixed, population-typical defaults for this phase — not tuned to any
    individual user's own baseline. Each metric that is `None` is simply
    not evaluated (not treated as a failure); if both are `None`, the rule
    passes with a "no data" explanation.
    """

    def __init__(
        self,
        *,
        maximum_resting_heart_rate: float = _DEFAULT_MAXIMUM_RESTING_HEART_RATE,
        minimum_heart_rate_variability: float = _DEFAULT_MINIMUM_HEART_RATE_VARIABILITY,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("readiness.recovery_metrics"),
            name="Recovery Metrics",
            description=(
                "Flags an elevated resting heart rate or a depressed heart rate variability."
            ),
            severity=severity,
        )
        self._maximum_resting_heart_rate = maximum_resting_heart_rate
        self._minimum_heart_rate_variability = minimum_heart_rate_variability

    def evaluate(self, context: ReadinessRuleContext) -> RuleResult:
        resting_heart_rate = context.resting_heart_rate
        heart_rate_variability = context.heart_rate_variability

        if resting_heart_rate is None and heart_rate_variability is None:
            return self._pass("No resting heart rate or heart rate variability recorded.")

        problems: list[str] = []

        if (
            resting_heart_rate is not None
            and resting_heart_rate.value > self._maximum_resting_heart_rate
        ):
            problems.append(
                f"resting heart rate of {resting_heart_rate.value:.0f} bpm exceeds the "
                f"maximum of {self._maximum_resting_heart_rate:.0f} bpm"
            )

        if (
            heart_rate_variability is not None
            and heart_rate_variability.value < self._minimum_heart_rate_variability
        ):
            problems.append(
                f"heart rate variability of {heart_rate_variability.value:.0f} ms is below the "
                f"minimum of {self._minimum_heart_rate_variability:.0f} ms"
            )

        if not problems:
            return self._pass("Resting heart rate and heart rate variability are within range.")

        return self._fail(
            "; ".join(problems).capitalize() + ".",
            recommendations=(
                Recommendation(
                    severity=self.severity,
                    message="Consider an easier session today and re-check tomorrow's readings.",
                ),
            ),
        )
