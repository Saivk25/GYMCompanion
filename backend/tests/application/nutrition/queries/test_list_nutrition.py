"""Tests for app/application/nutrition/queries/list_nutrition.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.nutrition.queries.list_nutrition import ListNutritionQuery
from app.application.shared.query import Query
from app.domain.user.identifiers import UserId


@pytest.mark.unit
def test_list_nutrition_query_is_a_query() -> None:
    assert isinstance(ListNutritionQuery(user_id=UserId.generate()), Query)


@pytest.mark.unit
def test_list_nutrition_query_exposes_its_user_id() -> None:
    user_id = UserId.generate()
    query = ListNutritionQuery(user_id=user_id)
    assert query.user_id == user_id


@pytest.mark.unit
def test_list_nutrition_query_is_immutable() -> None:
    query = ListNutritionQuery(user_id=UserId.generate())
    with pytest.raises(FrozenInstanceError):
        query.user_id = UserId.generate()  # type: ignore[misc]
