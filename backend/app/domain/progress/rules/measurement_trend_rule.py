"""`MeasurementTrendRule`: surfaces meaningful trends in the tape/body-
composition measurements `Progress` tracks beyond weight and body fat —
waist, chest, hip, arm, thigh, calf, neck, lean body mass, and muscle
mass — none of which `Goal` carries a target for.

Always passes, never fails — the same "always passes, this context
carries no data to fail it against" shape
`app.domain.goal.rules.strength_goal_rule.StrengthGoalRule` established
(ADR 0016): there is no target for any of these fields anywhere in this
codebase (`Goal` names only `target_weight`, `target_body_fat`,
`target_strength`), so there is nothing for this rule to compare against
and no "wrong direction" to fail on — only something to observe and
report, when there's enough data to observe it from. This is this
package's nearest equivalent to the Domain Model & Decision Engine
Bible's `Trend` entity ("a computed slope/direction over a metric's
history... requires a minimum sample size before being surfaced",
Section 5's catalog) for the measurement fields `BodyWeightRule`/
`BodyFatRule` don't cover — a deterministic, threshold-based
"did this move enough to be worth mentioning" check, not the actual
statistical slope computation a real `Trend` entity would need (that is
explicitly the Statistical layer's job, out of scope here).

One documented simplification: `minimum_change` is a single, shared
noise threshold applied uniformly across every measurement site, even
though different sites naturally vary by different amounts session to
session (waist circumference is far noisier than neck circumference).
Splitting this into a per-field threshold would be more accurate but
adds configuration surface this phase's task does not ask for; a future
increment with real user data to calibrate against could revisit this.
"""

from __future__ import annotations

from collections.abc import Callable

from app.domain.progress.context import ProgressContext
from app.domain.progress.rules.context import ProgressEvaluationRuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity

_DEFAULT_MINIMUM_ENTRIES = 2
_DEFAULT_MINIMUM_CHANGE = 1.0

# (display name, typed accessor) for every measurement field `Progress`
# tracks beyond body weight and body fat percentage — see the module
# docstring for why those two are excluded (they have their own
# dedicated rules, each comparing against a `Goal` target this rule has
# none of). Explicit accessor functions, not a dynamic `getattr(entry,
# name)` lookup, so mypy still checks every field name against
# `ProgressContext`'s real attributes rather than trusting a bare string.
_MEASUREMENT_FIELDS: tuple[tuple[str, Callable[[ProgressContext], float | None]], ...] = (
    ("waist", lambda entry: entry.waist.value if entry.waist is not None else None),
    ("chest", lambda entry: entry.chest.value if entry.chest is not None else None),
    ("hip", lambda entry: entry.hip.value if entry.hip is not None else None),
    ("arm", lambda entry: entry.arm.value if entry.arm is not None else None),
    ("thigh", lambda entry: entry.thigh.value if entry.thigh is not None else None),
    ("calf", lambda entry: entry.calf.value if entry.calf is not None else None),
    ("neck", lambda entry: entry.neck.value if entry.neck is not None else None),
    (
        "lean body mass",
        lambda entry: entry.lean_body_mass.value if entry.lean_body_mass is not None else None,
    ),
    (
        "muscle mass",
        lambda entry: entry.muscle_mass.value if entry.muscle_mass is not None else None,
    ),
)


def _values_for(
    progress_history: tuple[ProgressContext, ...],
    accessor: Callable[[ProgressContext], float | None],
) -> list[float]:
    return [value for entry in progress_history if (value := accessor(entry)) is not None]


class MeasurementTrendRule(Rule[ProgressEvaluationRuleContext]):
    """Always passes. When at least `minimum_entries` (2 by default)
    entries record a given measurement field and that field's value
    changed by at least `minimum_change` (1.0 by default, in whatever
    unit the record uses) between the earliest and latest such entry,
    names that field and the change in the explanation and attaches an
    informational `Recommendation`. Explains "no measurement data" or
    "no measurement trend beyond the noise threshold" when nothing
    qualifies."""

    def __init__(
        self,
        *,
        minimum_entries: int = _DEFAULT_MINIMUM_ENTRIES,
        minimum_change: float = _DEFAULT_MINIMUM_CHANGE,
        severity: RecommendationSeverity = RecommendationSeverity.ADVISORY,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("progress_evaluation.measurement_trend"),
            name="Measurement Trend",
            description="Surfaces meaningful trends in tape/body-composition measurements.",
            severity=severity,
        )
        self._minimum_entries = minimum_entries
        self._minimum_change = minimum_change

    def evaluate(self, context: ProgressEvaluationRuleContext) -> RuleResult:
        trending: list[str] = []
        any_field_had_enough_data = False

        for display_name, accessor in _MEASUREMENT_FIELDS:
            values = _values_for(context.progress_history, accessor)
            if len(values) < self._minimum_entries:
                continue
            any_field_had_enough_data = True

            change = values[-1] - values[0]
            if abs(change) >= self._minimum_change:
                direction = "increased" if change > 0 else "decreased"
                trending.append(f"{display_name} {direction} by {abs(change):.1f}")

        if not any_field_had_enough_data:
            return self._pass(
                f"No measurement field has at least {self._minimum_entries} recorded "
                "entries; cannot evaluate measurement trends."
            )

        if not trending:
            return self._pass(
                f"No measurement changed by at least {self._minimum_change} (the noise "
                "threshold) across the evaluated history."
            )

        summary = "; ".join(trending)
        return self._pass(
            f"Measurement trend(s) detected: {summary}.",
            recommendations=(
                Recommendation(
                    severity=self.severity, message=f"Notable measurement change(s): {summary}."
                ),
            ),
        )
