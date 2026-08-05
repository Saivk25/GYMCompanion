"""Tests for app/application/nutrition/queries/get_nutrition.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.nutrition.queries.get_nutrition import GetNutritionQuery
from app.application.shared.query import Query
from app.domain.nutrition.identifiers import NutritionId
from app.domain.user.identifiers import UserId


@pytest.mark.unit
def test_get_nutrition_query_is_a_query() -> None:
    assert isinstance(
        GetNutritionQuery(nutrition_id=NutritionId.generate(), requester_id=UserId.generate()),
        Query,
    )


@pytest.mark.unit
def test_get_nutrition_query_exposes_its_nutrition_id() -> None:
    nutrition_id = NutritionId.generate()
    query = GetNutritionQuery(nutrition_id=nutrition_id, requester_id=UserId.generate())
    assert query.nutrition_id == nutrition_id


@pytest.mark.unit
def test_get_nutrition_query_is_immutable() -> None:
    query = GetNutritionQuery(nutrition_id=NutritionId.generate(), requester_id=UserId.generate())
    with pytest.raises(FrozenInstanceError):
        query.nutrition_id = NutritionId.generate()  # type: ignore[misc]
