"""`NutritionRuleContext`: the `RuleContext` (`app.domain.rules`) subtype
every nutrition rule in this package evaluates against.

Deliberately narrower than the full `Nutrition` aggregate: only the six
fields the six rules in this package actually read. No `nutrition_id`, no
`user_id`, no `meal_type`/`source`, no `notes`, and — notably — no
`sugar`, even though `Nutrition` records it: this phase names exactly six
rules (Calories, Protein, Carbohydrates, Fat, Fiber, Hydration), and
`SugarRule` is not one of them. "`NutritionRuleContext` contains only the
nutrition information required by the rules" is this phase's own explicit
instruction, not just a style preference — the same reasoning
`app.domain.readiness.rules.context.ReadinessRuleContext`'s docstring
documents for the Readiness Rule Engine (Sprint 3, Phase 2).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.nutrition.nutrition import Nutrition
from app.domain.nutrition.value_objects import (
    Calories,
    Carbohydrates,
    Fat,
    Fiber,
    Protein,
    WaterIntake,
)
from app.domain.rules.context import RuleContext


@dataclass(frozen=True, kw_only=True)
class NutritionRuleContext(RuleContext):
    """One evaluation's worth of nutrition data. Every field is optional,
    matching `Nutrition`'s own fields — an entry with only some data
    recorded is normal (`Nutrition.record()` requires none of them), and
    each rule below is individually responsible for deciding what "no
    data for me" means (uniformly: pass, not fail — see each rule's own
    docstring, and this package's own `__init__.py` for why)."""

    calories: Calories | None = None
    protein: Protein | None = None
    carbohydrates: Carbohydrates | None = None
    fat: Fat | None = None
    fiber: Fiber | None = None
    water_intake: WaterIntake | None = None

    @classmethod
    def from_nutrition(cls, nutrition: Nutrition) -> NutritionRuleContext:
        """Builds a context from an already-loaded `Nutrition` aggregate.
        Takes the aggregate itself, not a `NutritionId` or a repository —
        this package declares no repository dependency of its own (per
        this phase's explicit "no repositories, no services" instruction);
        loading the `Nutrition` entry first is a caller concern.
        """
        return cls(
            calories=nutrition.calories,
            protein=nutrition.protein,
            carbohydrates=nutrition.carbohydrates,
            fat=nutrition.fat,
            fiber=nutrition.fiber,
            water_intake=nutrition.water_intake,
        )
