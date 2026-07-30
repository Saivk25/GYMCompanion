"""`ReadinessSafetyRule`: identifies an unsafe readiness state from a
`ReadinessContext` snapshot.

Not a duplicate of `app.domain.readiness.rules`' own five rules
(`SleepRule`, `EnergyRule`, `StressRule`, `SorenessRule`, `RecoveryRule`)
— those are general-purpose, WARNING-severity training *advice*
("consider a lighter session"). This rule asks a narrower, more
conservative question — "is it currently unsafe to train at all" — at
CRITICAL severity by default, evaluating sleep, stress, and heart-rate
signals together rather than field by field (soreness is deliberately
excluded here; see `soreness_rule.py` for why it gets its own rule in
this package instead).

The Domain Model & Decision Engine Bible's own red-flag mechanism (Table
50: "Red-flag override... GI/pain input at or above the severity
threshold... forces RecoveryState to Escalate, bypassing the rolling
formula entirely") is defined over `pain_flags`/`GI_symptoms` fields that
`ReadinessContext` does not carry — `app.domain.readiness`'s own README
entry already documents that omission ("routed through SafetyFlag, a
separate aggregate not built yet"). This rule is this codebase's nearest
deterministic equivalent given what `ReadinessContext` actually has:
critically low sleep, critically high stress, or an abnormal resting
heart rate/HRV pairing, each independently sufficient to trigger — not a
literal implementation of the Bible's GI/pain-specific override.
"""

from __future__ import annotations

from datetime import timedelta

from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity
from app.domain.safety.rules.context import SafetyRuleContext

_DEFAULT_CRITICAL_MINIMUM_SLEEP = timedelta(hours=3)
_DEFAULT_CRITICAL_STRESS = 9
_DEFAULT_CRITICAL_RESTING_HEART_RATE = 100.0
_DEFAULT_CRITICAL_HEART_RATE_VARIABILITY = 20.0


class ReadinessSafetyRule(Rule[SafetyRuleContext]):
    """Triggers when `context.readiness` shows sleep below
    `critical_minimum_sleep` (3 hours by default), stress at or above
    `critical_stress` (9 out of 10), or a resting heart rate at/above
    `critical_resting_heart_rate` (100 bpm) paired with an HRV at/below
    `critical_heart_rate_variability` (20 ms) — each an independently
    sufficient red flag. Passes, with an explanation, when
    `context.readiness` is `None` (no check-in supplied, cannot
    evaluate) or when none of the three signals are present/critical."""

    def __init__(
        self,
        *,
        critical_minimum_sleep: timedelta = _DEFAULT_CRITICAL_MINIMUM_SLEEP,
        critical_stress: int = _DEFAULT_CRITICAL_STRESS,
        critical_resting_heart_rate: float = _DEFAULT_CRITICAL_RESTING_HEART_RATE,
        critical_heart_rate_variability: float = _DEFAULT_CRITICAL_HEART_RATE_VARIABILITY,
        severity: RecommendationSeverity = RecommendationSeverity.CRITICAL,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("safety.readiness"),
            name="Readiness Safety",
            description=(
                "Identifies an unsafe readiness state from sleep, stress, and heart signals."
            ),
            severity=severity,
        )
        self._critical_minimum_sleep = critical_minimum_sleep
        self._critical_stress = critical_stress
        self._critical_resting_heart_rate = critical_resting_heart_rate
        self._critical_heart_rate_variability = critical_heart_rate_variability

    def evaluate(self, context: SafetyRuleContext) -> RuleResult:
        readiness = context.readiness
        if readiness is None:
            return self._pass("No readiness check-in supplied; cannot evaluate readiness safety.")

        problems: list[str] = []

        if (
            readiness.sleep_duration is not None
            and readiness.sleep_duration.value < self._critical_minimum_sleep
        ):
            problems.append(f"sleep of {readiness.sleep_duration.value} is critically low")

        if (
            readiness.stress_level is not None
            and readiness.stress_level.value >= self._critical_stress
        ):
            problems.append(f"stress level of {readiness.stress_level.value} is critically high")

        if (
            readiness.resting_heart_rate is not None
            and readiness.heart_rate_variability is not None
            and readiness.resting_heart_rate.value >= self._critical_resting_heart_rate
            and readiness.heart_rate_variability.value <= self._critical_heart_rate_variability
        ):
            problems.append(
                f"resting heart rate of {readiness.resting_heart_rate.value:.0f} bpm with HRV of "
                f"{readiness.heart_rate_variability.value:.0f} ms is a critical combination"
            )

        if problems:
            return self._fail(
                "Unsafe readiness state detected: " + "; ".join(problems) + ".",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Readiness signals indicate it is not safe to train hard today — "
                        "rest or seek guidance before continuing.",
                    ),
                ),
            )

        return self._pass("No critical readiness signals detected.")
