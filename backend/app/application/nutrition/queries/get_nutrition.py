"""`GetNutritionQuery`: the input to `GetNutritionHandler`."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.query import Query
from app.domain.nutrition.identifiers import NutritionId


@dataclass(frozen=True, kw_only=True)
class GetNutritionQuery(Query):
    """Fetch one Nutrition entry's current state as a `NutritionDTO`."""

    nutrition_id: NutritionId
