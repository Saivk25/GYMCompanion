"""Request/response schemas for the Nutrition endpoints
(`app/api/routes/v1/nutrition.py`). See `common.py`'s module docstring
and `goal.py`'s module docstring (no duplicated range validation — every
bound already lives on the corresponding value object) for the
conventions this file follows.

`UpdateNutritionRequest`'s fields being optional-and-`None`-means-
"leave unchanged" (not "clear") mirrors `UpdateNutritionCommand`'s own
documented semantics exactly (`app.application.nutrition.commands.
update_nutrition`) — this schema carries that meaning through unchanged,
the same "a schema's `to_command()` must not invent a different meaning
for `None` than the command it builds already has" discipline every
schema in this package follows.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.api.schemas.common import unwrap, unwrap_optional
from app.application.nutrition.commands.record_nutrition import RecordNutritionCommand
from app.application.nutrition.commands.update_notes import UpdateNutritionNotesCommand
from app.application.nutrition.commands.update_nutrition import UpdateNutritionCommand
from app.application.nutrition.commands.update_water import UpdateWaterCommand
from app.application.nutrition.dto.nutrition_dto import NutritionDTO
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


class RecordNutritionRequest(BaseModel):
    """No `user_id` field — see `app.api.schemas.goal.CreateGoalRequest`'s
    identical docstring for why."""

    nutrition_date: date
    meal_type: MealType | None = None
    source: NutritionSource | None = None
    calories: float | None = None
    protein: float | None = None
    carbohydrates: float | None = None
    fat: float | None = None
    fiber: float | None = None
    sugar: float | None = None
    water_intake: float | None = None
    notes: str | None = None

    def to_command(self, user_id: UserId) -> RecordNutritionCommand:
        return RecordNutritionCommand(
            user_id=user_id,
            nutrition_date=NutritionDate(self.nutrition_date),
            meal_type=self.meal_type,
            source=self.source,
            calories=Calories(self.calories) if self.calories is not None else None,
            protein=Protein(self.protein) if self.protein is not None else None,
            carbohydrates=(
                Carbohydrates(self.carbohydrates) if self.carbohydrates is not None else None
            ),
            fat=Fat(self.fat) if self.fat is not None else None,
            fiber=Fiber(self.fiber) if self.fiber is not None else None,
            sugar=Sugar(self.sugar) if self.sugar is not None else None,
            water_intake=WaterIntake(self.water_intake) if self.water_intake is not None else None,
            notes=MealNotes(self.notes) if self.notes is not None else None,
        )


class UpdateNutritionRequest(BaseModel):
    """Every field left `None` keeps its current stored value — see the
    module docstring."""

    calories: float | None = None
    protein: float | None = None
    carbohydrates: float | None = None
    fat: float | None = None
    fiber: float | None = None
    sugar: float | None = None

    def to_command(self, nutrition_id: NutritionId) -> UpdateNutritionCommand:
        return UpdateNutritionCommand(
            nutrition_id=nutrition_id,
            calories=Calories(self.calories) if self.calories is not None else None,
            protein=Protein(self.protein) if self.protein is not None else None,
            carbohydrates=(
                Carbohydrates(self.carbohydrates) if self.carbohydrates is not None else None
            ),
            fat=Fat(self.fat) if self.fat is not None else None,
            fiber=Fiber(self.fiber) if self.fiber is not None else None,
            sugar=Sugar(self.sugar) if self.sugar is not None else None,
        )


class UpdateWaterRequest(BaseModel):
    water_intake: float

    def to_command(self, nutrition_id: NutritionId) -> UpdateWaterCommand:
        return UpdateWaterCommand(
            nutrition_id=nutrition_id, water_intake=WaterIntake(self.water_intake)
        )


class UpdateNutritionNotesRequest(BaseModel):
    notes: str

    def to_command(self, nutrition_id: NutritionId) -> UpdateNutritionNotesCommand:
        return UpdateNutritionNotesCommand(nutrition_id=nutrition_id, notes=MealNotes(self.notes))


class NutritionResponse(BaseModel):
    nutrition_id: str
    user_id: str
    nutrition_date: date
    recorded_at: str
    meal_type: MealType | None
    source: NutritionSource | None
    calories: float | None
    protein: float | None
    carbohydrates: float | None
    fat: float | None
    fiber: float | None
    sugar: float | None
    water_intake: float | None
    notes: str
    updated_at: str | None

    @classmethod
    def from_dto(cls, dto: NutritionDTO) -> NutritionResponse:
        return cls(
            nutrition_id=str(dto.nutrition_id),
            user_id=str(dto.user_id),
            nutrition_date=unwrap(dto.nutrition_date),
            recorded_at=dto.recorded_at.isoformat(),
            meal_type=dto.meal_type,
            source=dto.source,
            calories=unwrap_optional(dto.calories),
            protein=unwrap_optional(dto.protein),
            carbohydrates=unwrap_optional(dto.carbohydrates),
            fat=unwrap_optional(dto.fat),
            fiber=unwrap_optional(dto.fiber),
            sugar=unwrap_optional(dto.sugar),
            water_intake=unwrap_optional(dto.water_intake),
            notes=unwrap(dto.notes),
            updated_at=dto.updated_at.isoformat() if dto.updated_at is not None else None,
        )
