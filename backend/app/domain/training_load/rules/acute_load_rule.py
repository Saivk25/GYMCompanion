"""`AcuteLoadRule`: flags a short-term (default 7-day) accumulation of
training load exceeding a configurable ceiling.

"Acute load" is the standard sports-science term for training load
accumulated over a short recent window (commonly 7 days). See
`docs/adr/0020-training-load-supplied-summaries.md` for why this rule
and `LoadRatioRule`'s acute:chronic ratio are grounded in general
sports-science literature (e.g. Gabbett 2016's workload-injury
research), not the Product Bible directly — the Bible names "training
load" only as an input to `RecoveryState` (Section 2, Table 1) without
prescribing acute/chronic windowing or numeric thresholds, the same
"loosely related... a stated simplification" caveat
`docs/adr/0018-safety-rule-engine-composition-and-authority.md` already
placed on Safety's own `WorkloadRule`.
"""

from __future__ import annotations

from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity
from app.domain.training_load.rules.context import TrainingLoadRuleContext

_DEFAULT_WINDOW_DAYS = 7
_DEFAULT_MINIMUM_ENTRIES = 3
_DEFAULT_LOAD_CEILING = 5000.0


class AcuteLoadRule(Rule[TrainingLoadRuleContext]):
    """Triggers when the summed training load across the trailing
    `window_days`-day window (7 days by default) exceeds `load_ceiling`
    (5000, this phase's own generic choice, not a Bible-mandated
    figure — the application layer supplies `TrainingLoad` values in
    whatever units its own formula produces, so this default is a
    starting point a real deployment should tune, not a universal
    constant). Passes, with an explanation, when fewer than
    `minimum_entries` summaries fall within that window — too little
    evidence to call it a spike rather than normal day-to-day data
    sparsity.
    """

    def __init__(
        self,
        *,
        window_days: int = _DEFAULT_WINDOW_DAYS,
        minimum_entries: int = _DEFAULT_MINIMUM_ENTRIES,
        load_ceiling: float = _DEFAULT_LOAD_CEILING,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("training_load.acute_load"),
            name="Acute Load",
            description=(
                "Evaluates recent short-term training load against a configurable ceiling."
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
                f"window; at least {self._minimum_entries} are needed to evaluate acute load."
            )

        acute_load = sum(entry.load.value for entry in window)
        if acute_load > self._load_ceiling:
            return self._fail(
                f"Acute training load over the trailing {self._window_days} day(s) is "
                f"{acute_load:.0f}, exceeding the {self._load_ceiling:.0f} ceiling.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Recent training load is high — consider a lighter session "
                        "or extra recovery before adding more volume.",
                    ),
                ),
            )

        return self._pass(
            f"Acute training load over the trailing {self._window_days} day(s) is "
            f"{acute_load:.0f}, within the {self._load_ceiling:.0f} ceiling."
        )
