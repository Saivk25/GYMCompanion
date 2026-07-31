"""`ListNutritionQuery`: the input to `ListNutritionHandler`.

The first real caller of `NutritionRepository.list_by_user()`
(`app.domain.nutrition.repository`), added specifically for this query —
see that module's own docstring.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.query import Query
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class ListNutritionQuery(Query):
    """List every Nutrition entry belonging to one User, as
    `NutritionDTO`s."""

    user_id: UserId
