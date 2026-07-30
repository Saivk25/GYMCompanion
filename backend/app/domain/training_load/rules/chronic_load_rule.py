"""`ChronicLoadRule`: flags a sustained longer-term (default 28-day)
training load, expressed as a weekly-equivalent figure, exceeding a
configurable ceiling.

"Chronic load" is the standard sports-science companion term to acute
load — training load accumulated over a longer window (commonly 28
days / 4 weeks) and normalized to a per-week figure so it is directly
comparable to `AcuteLoadRule`'s 7-day sum. This is the same "coupled"
acute:chronic convention `LoadRatioRule` reuses for its ratio — see
`docs/adr/0020-training-load-supplied-summaries.md`.
"""

from __future__ import annotations

from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity
from app.domain.training_load.rules.context import TrainingLoadRuleContext

_DEFAULT_WINDOW_DAYS = 28
_DEFAULT_MINIMUM_ENTRIES = 14
_DEFAULT_LOAD_CEILING = 4500.0


def _weekly_equivalent_load(window_days: int, total_load: float) -> float:
    """Normalizes a window's summed load to a per-week figure so a
    28-day (or any other) window is directly comparable to
    `AcuteLoadRule`'s 7-day sum."""
    weeks = window_days / 7
    return total_load / weeks


class ChronicLoadRule(Rule[TrainingLoadRuleContext]):
    """Triggers when the trailing `window_days`-day window's (28 days
    by default) total training load, normalized to a weekly-equivalent
    figure, exceeds `load_ceiling` (4500, this phase's own generic
    choice — see `AcuteLoadRule`'s docstring for why these defaults are
    starting points, not universal constants). Passes, with an
    explanation, when fewer than `minimum_entries` summaries fall
    within that window — a sparse chronic window is not a reliable
    baseline.
    """

    def __init__(
        self,
        *,
        window_days: int = _DEFAULT_WINDOW_DAYS,
        minimum_entries: int = _DEFAULT_MINIMUM_ENTRIES,
        load_ceiling: float = _DEFAULT_LOAD_CEILING,
        severity: RecommendationSeverity = RecommendationSeverity.ADVISORY,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("training_load.chronic_load"),
            name="Chronic Load",
            description=(
                "Evaluates longer-term training load against a configurable weekly-"
                "equivalent ceiling."
            ),
            severity=severity,
        )
        self._window_days = window_days
        self._minimum_entries = minimum_entries
        self._load_ceiling = load_ceiling

    def evaluate(self, context: TrainingLoadRuleContext) -> RuleResult:
        window = context.trailing_window(window_days=self._window_days)
        if len(window) < self._minimum_entries:
            return self._pass(
                f"Only {len(window)} entr(y/ies) in the trailing {self._window_days}-day "
                f"window; at least {self._minimum_entries} are needed to evaluate chronic load."
            )

        total_load = sum(entry.load.value for entry in window)
        chronic_load = _weekly_equivalent_load(self._window_days, total_load)
        if chronic_load > self._load_ceiling:
            return self._fail(
                f"Chronic training load over the trailing {self._window_days} day(s) is "
                f"{chronic_load:.0f}/week, exceeding the {self._load_ceiling:.0f}/week ceiling.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Sustained training load is high over the past several "
                        "weeks — review the overall program for a planned lighter block.",
                    ),
                ),
            )

        return self._pass(
            f"Chronic training load over the trailing {self._window_days} day(s) is "
            f"{chronic_load:.0f}/week, within the {self._load_ceiling:.0f}/week ceiling."
        )
