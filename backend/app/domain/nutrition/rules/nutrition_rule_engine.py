"""`NutritionRuleEngine`: the Nutrition-specific configuration of the
shared `RuleEngine[NutritionRuleContext]` (`app.domain.rules.engine`),
evaluating all six nutrition rules by default.

A subclass, not a wrapper — but it overrides no behavior, the same
construction-only pattern
`app.domain.readiness.rules.readiness_rule_engine.ReadinessRuleEngine`
established in Sprint 3, Phase 2 and
`docs/adr/0013-rule-engine-foundation.md` (Phase 1) calls for: an
"instance of `RuleEngine[TheirContext]`," not a subclass overriding its
behavior. This class only wires up the six default rules and gives that
configuration a discoverable name and a zero-argument constructor.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.domain.nutrition.rules.calories_rule import CaloriesRule
from app.domain.nutrition.rules.carbohydrates_rule import CarbohydratesRule
from app.domain.nutrition.rules.context import NutritionRuleContext
from app.domain.nutrition.rules.fat_rule import FatRule
from app.domain.nutrition.rules.fiber_rule import FiberRule
from app.domain.nutrition.rules.hydration_rule import HydrationRule
from app.domain.nutrition.rules.protein_rule import ProteinRule
from app.domain.rules.engine import RuleEngine
from app.domain.rules.rule import Rule


def _default_rules() -> tuple[Rule[NutritionRuleContext], ...]:
    return (
        CaloriesRule(),
        ProteinRule(),
        CarbohydratesRule(),
        FatRule(),
        FiberRule(),
        HydrationRule(),
    )


class NutritionRuleEngine(RuleEngine[NutritionRuleContext]):
    """Evaluates a `NutritionRuleContext` against `CaloriesRule`,
    `ProteinRule`, `CarbohydratesRule`, `FatRule`, `FiberRule`, and
    `HydrationRule` by default, and aggregates their results into one
    `RuleResult` — see `RuleEngine.evaluate()` for exactly how
    passed/severity/explanation/recommendations/triggered_rules are
    combined.

    Accepts an explicit `rules` override for testing or for a caller that
    wants a subset/reconfigured set of nutrition rules; the six defaults
    are used when omitted.
    """

    def __init__(self, rules: Sequence[Rule[NutritionRuleContext]] | None = None) -> None:
        super().__init__(rules if rules is not None else _default_rules())
