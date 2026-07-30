"""`PlateauRule`: detects a prolonged lack of measurable progress — the
Domain Model & Decision Engine Bible's own plateau definition (Table 54:
"Requires a defined number of consecutive flat weeks — a single flat
week is never a plateau").

Goal-agnostic, unlike `BodyWeightRule`/`BodyFatRule`: a plateau is a real
observation about the body regardless of whether an active goal exists
to measure it against (the Bible's own `PlateauEvent` entity is defined
purely over "a metric's history", Section 5's catalog, with no mention of
`Goal`), so this rule applies no "Active goals only" guard and reads no
`context.goal` field at all.

Approximates the Bible's "consecutive flat weeks" as a configurable
count of consecutive *progress entries* instead — `Progress` enforces no
weekly logging cadence (unlike, say, a fixed check-in schedule), so
"weeks" has no direct analog in this codebase's data; a stated
simplification, not silently assumed away. Evaluates `body_weight`
first, since it is the most consistently logged metric across this
codebase's `Progress` records; falls back to `body_fat_percentage` only
when body weight doesn't have enough trailing data, so this rule always
prefers the metric more likely to actually be populated rather than
requiring both.
"""

from __future__ import annotations

from app.domain.progress.context import ProgressContext
from app.domain.progress.rules.context import ProgressEvaluationRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_MINIMUM_CONSECUTIVE_ENTRIES = 4
_DEFAULT_WEIGHT_PLATEAU_TOLERANCE = 1.0
_DEFAULT_BODY_FAT_PLATEAU_TOLERANCE = 1.0


def _trailing_weights(progress_history: tuple[ProgressContext, ...], count: int) -> list[float]:
    entries = [
        entry.body_weight.value for entry in progress_history if entry.body_weight is not None
    ]
    return entries[-count:]


def _trailing_body_fat(progress_history: tuple[ProgressContext, ...], count: int) -> list[float]:
    entries = [
        entry.body_fat_percentage.value
        for entry in progress_history
        if entry.body_fat_percentage is not None
    ]
    return entries[-count:]


class PlateauRule(Rule[ProgressEvaluationRuleContext]):
    """Triggers when the trailing `minimum_consecutive_entries` (4 by
    default) body-weight-bearing entries all fall within a range of
    `weight_plateau_tolerance` (1.0 by default) of each other — no
    meaningful movement across that whole window. Falls back to
    `body_fat_percentage` (tolerance `body_fat_plateau_tolerance`, also
    1.0 by default) when fewer than `minimum_consecutive_entries` entries
    record body weight. Passes when neither metric has enough trailing
    data, or when the trailing window's range exceeds its tolerance
    (meaningful movement detected)."""

    def __init__(
        self,
        *,
        minimum_consecutive_entries: int = _DEFAULT_MINIMUM_CONSECUTIVE_ENTRIES,
        weight_plateau_tolerance: float = _DEFAULT_WEIGHT_PLATEAU_TOLERANCE,
        body_fat_plateau_tolerance: float = _DEFAULT_BODY_FAT_PLATEAU_TOLERANCE,
        severity: RecommendationSeverity = RecommendationSeverity.ADVISORY,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("progress_evaluation.plateau"),
            name="Plateau",
            description="Detects a prolonged lack of measurable body-composition progress.",
            severity=severity,
        )
        self._minimum_consecutive_entries = minimum_consecutive_entries
        self._weight_plateau_tolerance = weight_plateau_tolerance
        self._body_fat_plateau_tolerance = body_fat_plateau_tolerance

    def evaluate(self, context: ProgressEvaluationRuleContext) -> RuleResult:
        weights = _trailing_weights(context.progress_history, self._minimum_consecutive_entries)
        if len(weights) >= self._minimum_consecutive_entries:
            return self._evaluate_window(
                metric_name="body weight",
                values=weights,
                tolerance=self._weight_plateau_tolerance,
            )

        body_fat = _trailing_body_fat(context.progress_history, self._minimum_consecutive_entries)
        if len(body_fat) >= self._minimum_consecutive_entries:
            return self._evaluate_window(
                metric_name="body fat percentage",
                values=body_fat,
                tolerance=self._body_fat_plateau_tolerance,
            )

        return self._pass(
            "Neither body weight nor body fat percentage has "
            f"{self._minimum_consecutive_entries} consecutive recorded entries; cannot "
            "assess a plateau."
        )

    def _evaluate_window(
        self, *, metric_name: str, values: list[float], tolerance: float
    ) -> RuleResult:
        window_range = max(values) - min(values)
        if window_range <= tolerance:
            return self._fail(
                f"{metric_name.capitalize()} has stayed within {window_range:.1f} across the "
                f"last {len(values)} entries — a plateau (tolerance: {tolerance}).",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message=f"{metric_name.capitalize()} has plateaued — consider adjusting "
                        "nutrition, training volume, or reviewing the current goal.",
                    ),
                ),
            )

        return self._pass(
            f"{metric_name.capitalize()} moved by {window_range:.1f} across the last "
            f"{len(values)} entries, beyond the {tolerance} plateau tolerance."
        )
