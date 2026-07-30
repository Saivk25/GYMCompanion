"""`ProgressiveOverloadRuleEngine`: the Progressive-Overload-specific
configuration of the shared `RuleEngine[ProgressiveOverloadRuleContext]`
(`app.domain.rules.engine`), evaluating all five progressive overload
rules by default.

A subclass, not a wrapper, that overrides no behavior — the same
"configuration-only subclass" shape `ReadinessRuleEngine`,
`NutritionRuleEngine`, and `GoalAlignmentRuleEngine` already establish;
see `docs/adr/0013-rule-engine-foundation.md`.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.domain.rules.engine import RuleEngine
from app.domain.rules.rule import Rule
from app.domain.workout.rules.context import ProgressiveOverloadRuleContext
from app.domain.workout.rules.deload_rule import DeloadRule
from app.domain.workout.rules.frequency_rule import FrequencyRule
from app.domain.workout.rules.intensity_rule import IntensityRule
from app.domain.workout.rules.progression_rule import ProgressionRule
from app.domain.workout.rules.volume_rule import VolumeRule


def _default_rules() -> tuple[Rule[ProgressiveOverloadRuleContext], ...]:
    return (
        VolumeRule(),
        IntensityRule(),
        FrequencyRule(),
        ProgressionRule(),
        DeloadRule(),
    )


class ProgressiveOverloadRuleEngine(RuleEngine[ProgressiveOverloadRuleContext]):
    """Evaluates a `ProgressiveOverloadRuleContext` against `VolumeRule`,
    `IntensityRule`, `FrequencyRule`, `ProgressionRule`, and `DeloadRule`
    by default, and aggregates their results into one `RuleResult` — see
    `RuleEngine.evaluate()` for exactly how passed/severity/explanation/
    recommendations/triggered_rules are combined.

    Accepts an explicit `rules` override for testing or for a caller that
    wants a subset/reconfigured set of progressive overload rules; the
    five defaults are used when omitted.
    """

    def __init__(self, rules: Sequence[Rule[ProgressiveOverloadRuleContext]] | None = None) -> None:
        super().__init__(rules if rules is not None else _default_rules())
