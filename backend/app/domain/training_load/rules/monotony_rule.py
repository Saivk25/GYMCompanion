"""`MonotonyRule`: flags training that is too *uniform* day-to-day —
low variability in daily load, a distinct risk signal from sheer
volume.

Implements Foster's training monotony (Foster 1998): the mean of daily
training loads divided by their standard deviation across a window. A
high monotony score means the athlete trained at roughly the same load
every day with little variation between hard and easy days — a pattern
independently associated with increased illness/injury/overtraining
risk even when total volume is otherwise reasonable, which is exactly
why this is its own rule rather than folded into `AcuteLoadRule` or
`ChronicLoadRule`. See
`docs/adr/0020-training-load-supplied-summaries.md` for the population-
standard-deviation simplification this rule makes (population, not
sample, standard deviation — a stated choice, not an oversight).
"""

from __future__ import annotations

from statistics import mean, pstdev

from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity
from app.domain.training_load.rules.context import TrainingLoadRuleContext

_DEFAULT_WINDOW_DAYS = 7
_DEFAULT_MINIMUM_ENTRIES = 4
_DEFAULT_MONOTONY_CEILING = 2.0


class MonotonyRule(Rule[TrainingLoadRuleContext]):
    """Triggers when the trailing `window_days`-day window's (7 days by
    default) training monotony — `mean(daily load) / stdev(daily
    load)` — exceeds `monotony_ceiling` (2.0 by default, the commonly
    cited Foster "high monotony" threshold; a generic literature-
    grounded default, not a Bible-mandated figure). Also triggers, as a
    special case, when every entry in the window carries the exact same
    non-zero load: standard deviation is then zero, making monotony
    mathematically unbounded rather than merely high — treated here as
    the worst case rather than an undefined result. Passes, with an
    explanation, when fewer than `minimum_entries` summaries fall
    within the window, or when the window's mean load is zero (no
    training logged — nothing to be monotonous about).
    """

    def __init__(
        self,
        *,
        window_days: int = _DEFAULT_WINDOW_DAYS,
        minimum_entries: int = _DEFAULT_MINIMUM_ENTRIES,
        monotony_ceiling: float = _DEFAULT_MONOTONY_CEILING,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("training_load.monotony"),
            name="Monotony",
            description="Evaluates whether training load variability is too low.",
            severity=severity,
        )
        self._window_days = window_days
        self._minimum_entries = minimum_entries
        self._monotony_ceiling = monotony_ceiling

    def evaluate(self, context: TrainingLoadRuleContext) -> RuleResult:
        window = context.trailing_window(window_days=self._window_days)
        if len(window) < self._minimum_entries:
            return self._pass(
                f"Only {len(window)} entr(y/ies) in the trailing {self._window_days}-day "
                f"window; at least {self._minimum_entries} are needed to evaluate monotony."
            )

        loads = [entry.load.value for entry in window]
        average_load = mean(loads)
        if average_load == 0:
            return self._pass(
                f"No training load logged in the trailing {self._window_days}-day window; "
                "nothing to evaluate for monotony."
            )

        load_stdev = pstdev(loads)
        if load_stdev == 0:
            return self._fail(
                f"Training load was identical ({average_load:.0f}) on every day of the "
                f"trailing {self._window_days}-day window — zero variability.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Training load has no variation day-to-day — mix in easier "
                        "and harder days rather than repeating the same load.",
                    ),
                ),
            )

        monotony = average_load / load_stdev
        if monotony > self._monotony_ceiling:
            return self._fail(
                f"Training monotony over the trailing {self._window_days} day(s) is "
                f"{monotony:.2f}, exceeding the {self._monotony_ceiling:.2f} ceiling.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Training load is too uniform day-to-day — mix in easier "
                        "and harder days to lower monotony.",
                    ),
                ),
            )

        return self._pass(
            f"Training monotony over the trailing {self._window_days} day(s) is "
            f"{monotony:.2f}, within the {self._monotony_ceiling:.2f} ceiling."
        )
