"""`NutritionSqlRepository`: the SQLAlchemy-backed implementation of
`app.domain.nutrition.repository.NutritionRepository`.

See `workout_repository.py`'s module docstring for the tenant-scoping shape
this repository follows.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.domain.nutrition.enums import MealType, NutritionSource
from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.nutrition import Nutrition
from app.domain.nutrition.repository import NutritionRepository
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
from app.infra.database import tenant_scope
from app.infra.models.nutrition import NutritionRow
from app.infra.repositories._tracking import TrackingRepository


class NutritionSqlRepository(
    NutritionRepository, TrackingRepository[Nutrition, NutritionId, NutritionRow]
):
    """Postgres-backed `NutritionRepository`. See the module docstring for
    the tenant-scoping shape."""

    def get(self, entity_id: NutritionId) -> Nutrition | None:
        row = self._session.get(NutritionRow, entity_id.value)
        if row is None:
            return None
        nutrition = _to_domain(row)
        self._track(entity_id, nutrition, row)
        return nutrition

    def add(self, aggregate: Nutrition) -> None:
        with tenant_scope(self._session, str(aggregate.user_id)):
            row = NutritionRow(nutrition_id=aggregate.id.value, user_id=aggregate.user_id.value)
            self._apply_to_row(aggregate, row)
            self._session.add(row)
        self._track(aggregate.id, aggregate, row)

    def remove(self, aggregate: Nutrition) -> None:
        with tenant_scope(self._session, str(aggregate.user_id)):
            row = self._session.get(NutritionRow, aggregate.id.value)
            if row is not None:
                self._session.delete(row)
        self._untrack(aggregate.id)

    def list_by_user(self, user_id: UserId) -> Sequence[Nutrition]:
        with tenant_scope(self._session, str(user_id)):
            rows = self._session.scalars(
                select(NutritionRow).where(NutritionRow.user_id == user_id.value)
            ).all()
        entries = []
        for row in rows:
            nutrition = _to_domain(row)
            self._track(nutrition.id, nutrition, row)
            entries.append(nutrition)
        return entries

    def _apply_to_row(self, aggregate: Nutrition, row: NutritionRow) -> None:
        row.nutrition_date = aggregate.nutrition_date.value
        row.meal_type = aggregate.meal_type.value if aggregate.meal_type is not None else None
        row.source = aggregate.source.value if aggregate.source is not None else None
        row.calories = aggregate.calories.value if aggregate.calories is not None else None
        row.protein = aggregate.protein.value if aggregate.protein is not None else None
        row.carbohydrates = (
            aggregate.carbohydrates.value if aggregate.carbohydrates is not None else None
        )
        row.fat = aggregate.fat.value if aggregate.fat is not None else None
        row.fiber = aggregate.fiber.value if aggregate.fiber is not None else None
        row.sugar = aggregate.sugar.value if aggregate.sugar is not None else None
        row.water_intake = (
            aggregate.water_intake.value if aggregate.water_intake is not None else None
        )
        row.notes = aggregate.notes.value
        row.updated_at = aggregate.updated_at


def _to_domain(row: NutritionRow) -> Nutrition:
    return Nutrition(
        NutritionId(row.nutrition_id),
        user_id=UserId(row.user_id),
        nutrition_date=NutritionDate(row.nutrition_date),
        recorded_at=row.recorded_at,
        meal_type=MealType(row.meal_type) if row.meal_type is not None else None,
        source=NutritionSource(row.source) if row.source is not None else None,
        calories=Calories(row.calories) if row.calories is not None else None,
        protein=Protein(row.protein) if row.protein is not None else None,
        carbohydrates=Carbohydrates(row.carbohydrates) if row.carbohydrates is not None else None,
        fat=Fat(row.fat) if row.fat is not None else None,
        fiber=Fiber(row.fiber) if row.fiber is not None else None,
        sugar=Sugar(row.sugar) if row.sugar is not None else None,
        water_intake=WaterIntake(row.water_intake) if row.water_intake is not None else None,
        notes=MealNotes(row.notes),
        updated_at=row.updated_at,
    )
