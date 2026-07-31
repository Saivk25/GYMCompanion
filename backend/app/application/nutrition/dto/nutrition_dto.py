"""`NutritionDTO`: the read-only projection of a `Nutrition` aggregate
returned to whatever calls a Nutrition query handler.

Not the same type as `app.domain.nutrition.context.NutritionContext` —
identical reasoning to `WorkoutDTO`'s own module docstring
(`app.application.workout.dto.workout_dto`): `NutritionContext` is
scoped to a future domain service (a NutritionPattern-equivalent
weekly-consistency read model, meal-plan generation — neither built
yet), one-directional, and never crosses the Application Layer
boundary; `NutritionDTO` is this layer's own read projection for
`GetNutritionHandler`/`ListNutritionHandler`, a different consumer
with different reasons to change independently. See
`docs/adr/0025-nutrition-application-use-cases.md`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
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
from app.domain.user.identifiers import UserId

if TYPE_CHECKING:
    # Import only for the type checker — see UserDTO's identical note
    # for why this avoids a real circular import at module load time.
    from app.domain.nutrition.nutrition import Nutrition


@dataclass(frozen=True, kw_only=True)
class NutritionDTO:
    """An immutable, read-only snapshot of one `Nutrition` entry, taken
    at query time."""

    nutrition_id: NutritionId
    user_id: UserId
    nutrition_date: NutritionDate
    recorded_at: datetime
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
    updated_at: datetime | None

    @classmethod
    def from_nutrition(cls, nutrition: Nutrition) -> NutritionDTO:
        """Builds a DTO from a live `Nutrition` aggregate. One-
        directional on purpose, mirroring `WorkoutDTO.from_workout` —
        `Nutrition` never depends on this type.
        """
        return cls(
            nutrition_id=nutrition.id,
            user_id=nutrition.user_id,
            nutrition_date=nutrition.nutrition_date,
            recorded_at=nutrition.recorded_at,
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
            updated_at=nutrition.updated_at,
        )
