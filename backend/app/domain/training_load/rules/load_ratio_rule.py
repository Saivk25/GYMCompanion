"""`LoadRatioRule`: evaluates the acute-to-chronic training load ratio
("ACWR" in the sports-science literature) against a configured "sweet
spot" range.

Uses the same "coupled" convention `ChronicLoadRule` establishes:
acute load is the trailing 7-day sum, chronic load is the trailing
28-day sum normalized to a weekly-equivalent figure, and the ratio is
acute divided by chronic. A ratio well above 1.0 means recent load has
spiked relative to the established baseline ("too much, too soon" —
Gabbett 2016); a ratio well below 1.0 means recent load has dropped
well below the baseline (a detraining signal, and itself a documented
re-exposure risk when training resumes at the old baseline intensity).
This is the same general concept `SorenessRule`'s sibling in
`app.domain.safety.rules.workload_rule.WorkloadRule` uses, at a
different, simpler two-window ratio — see
`docs/adr/0020-training-load-supplied-summaries.md` for exactly how
this rule differs from that one and from Progressive Overload's
`DeloadRule`, so the overlap is understood as deliberate, not
accidental duplication.
"""

from __future__ import annotations

from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity
from app.domain.training_load.rules.context import TrainingLoadRuleContext

_DEFAULT_ACUTE_WINDOW_DAYS = 7
_DEFAULT_CHRONIC_WINDOW_DAYS = 28
_DEFAULT_MINIMUM_CHRONIC_ENTRIES = 14
_DEFAULT_LOW_RATIO_THRESHOLD = 0.8
_DEFAULT_HIGH_RATIO_THRESHOLD = 1.5


def _weekly_equivalent_load(window_days: int, total_load: float) -> float:
    weeks = window_days / 7
    return total_load / weeks


class LoadRatioRule(Rule[TrainingLoadRuleContext]):
    """Triggers when the acute:chronic load ratio falls outside
    `[low_ratio_threshold, high_ratio_threshold]` (0.8-1.5 by default —
    the commonly cited sports-science "sweet spot" and "high risk"
    boundary, e.g. Gabbett 2016; a generic literature-grounded default,
    not a Bible-mandated or personalized figure). Passes, with an
    explanation, when there are fewer than `minimum_chronic_entries`
    summaries in the chronic window (no reliable baseline to compare
    against) or when the chronic window's total load is zero (nothing
    to divide by — a genuinely fresh training history, not an error).
    """

    def __init__(
        self,
        *,
        acute_window_days: int = _DEFAULT_ACUTE_WINDOW_DAYS,
        chronic_window_days: int = _DEFAULT_CHRONIC_WINDOW_DAYS,
        minimum_chronic_entries: int = _DEFAULT_MINIMUM_CHRONIC_ENTRIES,
        low_ratio_threshold: float = _DEFAULT_LOW_RATIO_THRESHOLD,
        high_ratio_threshold: float = _DEFAULT_HIGH_RATIO_THRESHOLD,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("training_load.load_ratio"),
            name="Load Ratio",
            description="Evaluates the acute-to-chronic training load ratio.",
            severity=severity,
        )
        self._acute_window_days = acute_window_days
        self._chronic_window_days = chronic_window_days
        self._minimum_chronic_entries = minimum_chronic_entries
        self._low_ratio_threshold = low_ratio_threshold
        self._high_ratio_threshold = high_ratio_threshold

    def evaluate(self, context: TrainingLoadRuleContext) -> RuleResult:
        chronic_window = context.trailing_window(window_days=self._chronic_window_days)
        if len(chronic_window) < self._minimum_chronic_entries:
            return self._pass(
                f"Only {len(chronic_window)} entr(y/ies) in the trailing "
                f"{self._chronic_window_days}-day chronic window; at least "
                f"{self._minimum_chronic_entries} are needed to establish a baseline."
            )

        chronic_total = sum(entry.load.value for entry in chronic_window)
        chronic_load = _weekly_equivalent_load(self._chronic_window_days, chronic_total)
        if chronic_load == 0:
            return self._pass(
                "Chronic training load is zero; no baseline to compute an acute:chronic "
                "ratio against."
            )

        acute_window = context.trailing_window(window_days=self._acute_window_days)
        acute_total = sum(entry.load.value for entry in acute_window)
        acute_load = _weekly_equivalent_load(self._acute_window_days, acute_total)
        ratio = acute_load / chronic_load

        if ratio > self._high_ratio_threshold:
            return self._fail(
                f"Acute:chronic load ratio is {ratio:.2f}, above the "
                f"{self._high_ratio_threshold:.2f} high-risk threshold.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Recent training load has spiked well above the established "
                        "baseline — ease the ramp-up to reduce injury risk.",
                    ),
                ),
            )

        if ratio < self._low_ratio_threshold:
            return self._fail(
                f"Acute:chronic load ratio is {ratio:.2f}, below the "
                f"{self._low_ratio_threshold:.2f} low threshold.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Recent training load has dropped well below the established "
                        "baseline — ease back in gradually rather than resuming at the old "
                        "intensity.",
                    ),
                ),
            )

        return self._pass(
            f"Acute:chronic load ratio is {ratio:.2f}, within the "
            f"{self._low_ratio_threshold:.2f}-{self._high_ratio_threshold:.2f} range."
        )
