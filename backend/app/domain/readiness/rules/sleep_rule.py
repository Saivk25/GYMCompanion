"""`SleepRule`: flags a night's sleep shorter than a configured minimum.

Deliberately a single fixed threshold against one night's `SleepDuration`
— no trend, no rolling average, no adjustment for a user's personal
baseline. That kind of comparison belongs to `RecoveryState` (Domain
Model & Decision Engine Bible, Section 4.8's sibling entity, "the rolling,
derived state built from a window of check-ins plus training load"), not
built in this phase; see `docs/adr/0014-readiness-rule-composition.md`.
"""

from __future__ import annotations

from datetime import timedelta

from app.domain.readiness.rules.context import ReadinessRuleContext
from app.domain.readiness.value_objects import SleepDuration
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_MINIMUM_SLEEP = timedelta(hours=7)


class SleepRule(Rule[ReadinessRuleContext]):
    """Triggers when `context.sleep_duration` is below `minimum_sleep`
    (seven hours by default — a common general sleep-hygiene guideline,
    this phase's own choice, not a Bible-mandated figure; a future
    increment may make this experience-tier- or user-specific). Passes,
    with no recommendation, when `context.sleep_duration` is `None` — a
    missing observation is not evidence of a problem.
    """

    def __init__(
        self,
        *,
        minimum_sleep: timedelta = _DEFAULT_MINIMUM_SLEEP,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("readiness.sleep_duration"),
            name="Sleep Duration",
            description="Flags a night's sleep shorter than the configured minimum.",
            severity=severity,
        )
        self._minimum_sleep = minimum_sleep

    def evaluate(self, context: ReadinessRuleContext) -> RuleResult:
        sleep_duration = context.sleep_duration
        if sleep_duration is None:
            return self._pass("No sleep duration recorded.")

        if sleep_duration.value >= self._minimum_sleep:
            return self._pass(
                f"Sleep duration of {_format_duration(sleep_duration)} "
                f"meets the {_format_duration_value(self._minimum_sleep)} minimum."
            )

        return self._fail(
            f"Sleep duration of {_format_duration(sleep_duration)} is below the "
            f"{_format_duration_value(self._minimum_sleep)} minimum.",
            recommendations=(
                Recommendation(
                    severity=self.severity,
                    message="Prioritize an earlier bedtime tonight to catch up on sleep.",
                ),
            ),
        )


def _format_duration(sleep_duration: SleepDuration) -> str:
    return _format_duration_value(sleep_duration.value)


def _format_duration_value(value: timedelta) -> str:
    hours = value.total_seconds() / 3600
    return f"{hours:.1f}h"
