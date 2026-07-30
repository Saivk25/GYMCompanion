"""The Nutrition Rule Engine: Sprint 3 Phase 3's second concrete
deterministic rule engine, built on the Phase 1 Rule Engine foundation
(`app.domain.rules`) and the Nutrition aggregate
(`app.domain.nutrition`), following the same pattern
`app.domain.readiness.rules` (Sprint 3, Phase 2) established.

This engine evaluates a user's logged nutrition intake and produces
deterministic `Recommendation`s only — no AI, no meal planning, no food
database lookup, no barcode scanning, no macro recommendations, and no
personalized calorie targets (the Bible's `MacroFactor`-equivalent
adaptive calculation from real intake and weight trend is explicitly not
built here).

Six independent rules (`CaloriesRule`, `ProteinRule`,
`CarbohydratesRule`, `FatRule`, `FiberRule`, `HydrationRule`), each
validating one field of `NutritionRuleContext` against a configurable
`[minimum, maximum]` range, composed by `NutritionRuleEngine` (itself a
thin, behavior-preserving configuration of the shared
`RuleEngine[NutritionRuleContext]`). See
`docs/adr/0014-readiness-rule-composition.md` for the independent-rule
composition strategy this package continues (Sprint 3 Phase 2's ADR,
still the governing rationale — see this package's own rule modules for
the one genuinely Nutrition-specific addition: dual minimum/maximum
thresholds per rule, rather than Readiness's single-threshold shape).

Depends on nothing outside the Python standard library,
`app.domain.shared_kernel`, `app.domain.rules` (the Phase 1 foundation),
and `app.domain.nutrition` (its own parent aggregate) — enforced by the
same statically-checked rule as the rest of `app/domain`
(`tests/domain/test_import_boundaries.py`).
"""

from app.domain.nutrition.rules.calories_rule import CaloriesRule
from app.domain.nutrition.rules.carbohydrates_rule import CarbohydratesRule
from app.domain.nutrition.rules.context import NutritionRuleContext
from app.domain.nutrition.rules.fat_rule import FatRule
from app.domain.nutrition.rules.fiber_rule import FiberRule
from app.domain.nutrition.rules.hydration_rule import HydrationRule
from app.domain.nutrition.rules.nutrition_rule_engine import NutritionRuleEngine
from app.domain.nutrition.rules.protein_rule import ProteinRule

__all__ = [
    "CaloriesRule",
    "CarbohydratesRule",
    "FatRule",
    "FiberRule",
    "HydrationRule",
    "NutritionRuleContext",
    "NutritionRuleEngine",
    "ProteinRule",
]
