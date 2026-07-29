"""`NutritionContext`: a read-only snapshot of a Nutrition entry for domain
services.

Same purpose as `UserContext`, `WorkoutContext`, `ExerciseContext`,
`WorkoutSessionContext`, and `ProgressContext`: lets a future domain
service — a NutritionPattern-equivalent weekly-consistency read model,
meal-plan generation, none built yet — consume everything it needs to
know about one entry in a single immutable value.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.domain.nutrition.enums import MealType, NutritionSource
from app.domain.nutrition.identifiers import NutritionId
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
from app.domain.shared_kernel.value_object import ValueObject
from app.domain.user.identifiers import UserId

if TYPE_CHECKING:
    # Import only for the type checker — see UserContext's identical note
    # for why this avoids a real circular import at module load time.
    from app.domain.nutrition.nutrition import Nutrition


@dataclass(frozen=True, kw_only=True)
class NutritionContext(ValueObject):
    """An immutable snapshot of one Nutrition entry, taken at a point in
    time."""

    nutrition_id: NutritionId
    user_id: UserId
    nutrition_date: NutritionDate
    meal_type: MealType | None
    source: NutritionSource | None
    calories: Calories | None
    protein: Protein | None
    carbohydrates: Carbohydrates | None
    fat: Fat | None
    fiber: Fiber | None
    sugar: Sugar | None
    water_intake: WaterIntake | None
    notes: MealNotes

    @classmethod
    def from_nutrition(cls, nutrition: Nutrition) -> NutritionContext:
        """Builds a snapshot from a live `Nutrition` aggregate. One-
        directional on purpose: `Nutrition` does not know this type
        exists.
        """
        return cls(
            nutrition_id=nutrition.id,
            user_id=nutrition.user_id,
            nutrition_date=nutrition.nutrition_date,
            meal_type=nutrition.meal_type,
            source=nutrition.source,
            calories=nutrition.calories,
            protein=nutrition.protein,
            carbohydrates=nutrition.carbohydrates,
            fat=nutrition.fat,
            fiber=nutrition.fiber,
            sugar=nutrition.sugar,
            water_intake=nutrition.water_intake,
            notes=nutrition.notes,
        )
