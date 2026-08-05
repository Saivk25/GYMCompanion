"""`GetNutritionQuery`: the input to `GetNutritionHandler`."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.query import Query
from app.domain.nutrition.identifiers import NutritionId
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class GetNutritionQuery(Query):
    """Fetch one Nutrition entry's current state as a `NutritionDTO`.

    `requester_id` is the authenticated caller — `GetNutritionHandler`
    compares it against the loaded entry's own `user_id` via
    `app.application.shared.ownership.ensure_owner` before returning it.
    See `docs/adr/0033-resource-ownership-authorization.md`.
    """

    nutrition_id: NutritionId
    requester_id: UserId
