"""`StrainRule`: flags excessive cumulative training strain — the
combination of *how much* was trained and *how uniform* it was.

Implements Foster's training strain (Foster 1998): the trailing
window's total training load multiplied by its monotony (see
`monotony_rule.py`'s own docstring for monotony's definition and the
population-standard-deviation simplification both rules share).
Strain is the standard companion metric to monotony in that literature
— a high-volume week trained with hard/easy variation carries lower
strain than the same volume trained at a uniform load every day, which
is exactly the interaction `AcuteLoadRule` and `MonotonyRule` alone
cannot each capture on their own. See
`docs/adr/0020-training-load-supplied-summaries.md`.
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
_DEFAULT_STRAIN_CEILING = 10000.0


class StrainRule(Rule[TrainingLoadRuleContext]):
    """Triggers when the trailing `window_days`-day window's (7 days by
    default) training strain — `sum(daily load) x monotony` — exceeds
    `strain_ceiling` (10000 by default, this phase's own generic
    choice — see `AcuteLoadRule`'s docstring for why these defaults are
    starting points, not universal constants). Also triggers, as a
    special case mirroring `MonotonyRule`'s own, when every entry in
    the window carries the exact same non-zero load: monotony is then
    mathematically unbounded, so strain is treated as the worst case
    rather than computed as an undefined product. Passes, with an
    explanation, when fewer than `minimum_entries` summaries fall
    within the window, or when the window's mean load is zero (no
    training logged).
    """

    def __init__(
        self,
        *,
        window_days: int = _DEFAULT_WINDOW_DAYS,
        minimum_entries: int = _DEFAULT_MINIMUM_ENTRIES,
        strain_ceiling: float = _DEFAULT_STRAIN_CEILING,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("training_load.strain"),
            name="Strain",
            description="Evaluates cumulative training strain from supplied load summaries.",
            severity=severity,
        )
        self._window_days = window_days
        self._minimum_entries = minimum_entries
        self._strain_ceiling = strain_ceiling

    def evaluate(self, context: TrainingLoadRuleContext) -> RuleResult:
        window = context.trailing_window(window_days=self._window_days)
        if len(window) < self._minimum_entries:
            return self._pass(
                f"Only {len(window)} entr(y/ies) in the trailing {self._window_days}-day "
                f"window; at least {self._minimum_entries} are needed to evaluate strain."
            )

        loads = [entry.load.value for entry in window]
        total_load = sum(loads)
        average_load = mean(loads)
        if average_load == 0:
            return self._pass(
                f"No training load logged in the trailing {self._window_days}-day window; "
                "nothing to evaluate for strain."
            )

        load_stdev = pstdev(loads)
        if load_stdev == 0:
            return self._fail(
                f"Training load was identical on every day of the trailing "
                f"{self._window_days}-day window, so strain is unbounded rather than merely "
                f"high (total load: {total_load:.0f}).",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Training load has no day-to-day variation, which drives "
                        "strain to its worst case regardless of total volume — mix in "
                        "easier and harder days.",
                    ),
                ),
            )

        monotony = average_load / load_stdev
        strain = total_load * monotony
        if strain > self._strain_ceiling:
            return self._fail(
                f"Training strain over the trailing {self._window_days} day(s) is "
                f"{strain:.0f}, exceeding the {self._strain_ceiling:.0f} ceiling.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Cumulative training strain is high — reduce total load, "
                        "add more day-to-day variation, or both.",
                    ),
                ),
            )

        return self._pass(
            f"Training strain over the trailing {self._window_days} day(s) is "
            f"{strain:.0f}, within the {self._strain_ceiling:.0f} ceiling."
        )
