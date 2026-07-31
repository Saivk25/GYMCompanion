"""`RecordNutritionCommand`: the input to `RecordNutritionHandler`.

Mirrors `Nutrition.record(...)`'s own keyword shape exactly: every
macro/water/meal field is optional, matching the aggregate's own
"everything can be supplied now or filled in afterward" design
(`nutrition.py`'s class docstring). Carries `user_id` because, unlike
`UpdateNutritionCommand`/`UpdateWaterCommand`/`DeleteNutritionCommand`
(which target an existing entry by `NutritionId`), this command creates
a brand-new entry with no id yet — the same "creation command carries
the owner id, mutation commands carry the aggregate id" split
`CreateWorkoutCommand`/`UpdateWorkoutCommand` already establish.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.nutrition.enums import MealType, NutritionSource
from app.domain.nutrition.value_objects import (
    Calories,
    Carbohydrates,
    Fat,
    Fiber,
    MealNotes,
    NutritionDate,
    Protein,
    Sugar,
    WaterIntake,
)
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class RecordNutritionCommand(Command):
    """Record a brand-new Nutrition entry for a User."""

    user_id: UserId
    nutrition_date: NutritionDate
    meal_type: MealType | None = None
    source: NutritionSource | None = None
    calories: Calories | None = None
    protein: Protein | None = None
    carbohydrates: Carbohydrates | None = None
    fat: Fat | None = None
    fiber: Fiber | None = None
    sugar: Sugar | None = None
    water_intake: WaterIntake | None = None
    notes: MealNotes | None = None
