"""`ProgressEvaluationRuleEngine`: the Progress-Evaluation-specific
configuration of the shared `RuleEngine[ProgressEvaluationRuleContext]`
(`app.domain.rules.engine`), evaluating all five progress evaluation
rules by default.

A subclass, not a wrapper, that overrides no behavior — the same
"configuration-only subclass" shape every prior concrete engine
establishes; see `docs/adr/0013-rule-engine-foundation.md`.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.domain.progress.rules.body_fat_rule import BodyFatRule
from app.domain.progress.rules.body_weight_rule import BodyWeightRule
from app.domain.progress.rules.consistency_rule import ConsistencyRule
from app.domain.progress.rules.context import ProgressEvaluationRuleContext
from app.domain.progress.rules.measurement_trend_rule import MeasurementTrendRule
from app.domain.progress.rules.plateau_rule import PlateauRule
from app.domain.rules.engine import RuleEngine
from app.domain.rules.rule import Rule


def _default_rules() -> tuple[Rule[ProgressEvaluationRuleContext], ...]:
    return (
        BodyWeightRule(),
        BodyFatRule(),
        MeasurementTrendRule(),
        ConsistencyRule(),
        PlateauRule(),
    )


class ProgressEvaluationRuleEngine(RuleEngine[ProgressEvaluationRuleContext]):
    """Evaluates a `ProgressEvaluationRuleContext` against
    `BodyWeightRule`, `BodyFatRule`, `MeasurementTrendRule`,
    `ConsistencyRule`, and `PlateauRule` by default, and aggregates their
    results into one `RuleResult` — see `RuleEngine.evaluate()` for
    exactly how passed/severity/explanation/recommendations/
    triggered_rules are combined.

    Accepts an explicit `rules` override for testing or for a caller that
    wants a subset/reconfigured set of progress evaluation rules; the
    five defaults are used when omitted.
    """

    def __init__(self, rules: Sequence[Rule[ProgressEvaluationRuleContext]] | None = None) -> None:
        super().__init__(rules if rules is not None else _default_rules())
