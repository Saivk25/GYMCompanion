"""Tests for app/application/nutrition/handlers/get_nutrition_handler.py."""

import pytest

from app.application.nutrition.handlers.get_nutrition_handler import GetNutritionHandler
from app.application.nutrition.queries.get_nutrition import GetNutritionQuery
from app.domain.nutrition.identifiers import NutritionId
from app.domain.user.identifiers import UserId
from tests.application.nutrition.factories import (
    FakeNutritionRepository,
    FakeUnitOfWork,
    a_recorded_nutrition,
)


@pytest.mark.unit
def test_returns_a_nutrition_dto_for_an_existing_entry() -> None:
    nutrition = a_recorded_nutrition()
    uow = FakeUnitOfWork(entries=FakeNutritionRepository({nutrition.id: nutrition}))
    handler = GetNutritionHandler(uow=uow)

    result = handler.handle(
        GetNutritionQuery(nutrition_id=nutrition.id, requester_id=nutrition.user_id)
    )

    assert result.success is True
    assert result.value is not None
    assert result.value.nutrition_id == nutrition.id
    assert result.value.user_id == nutrition.user_id


@pytest.mark.unit
def test_a_missing_nutrition_entry_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork()
    handler = GetNutritionHandler(uow=uow)
    missing_id = NutritionId.generate()

    result = handler.handle(
        GetNutritionQuery(nutrition_id=missing_id, requester_id=UserId.generate())
    )

    assert result.success is False
    assert str(missing_id) in result.errors[0]


@pytest.mark.unit
def test_a_requester_who_does_not_own_the_entry_is_forbidden() -> None:
    nutrition = a_recorded_nutrition()
    uow = FakeUnitOfWork(entries=FakeNutritionRepository({nutrition.id: nutrition}))
    handler = GetNutritionHandler(uow=uow)

    result = handler.handle(
        GetNutritionQuery(nutrition_id=nutrition.id, requester_id=UserId.generate())
    )

    assert result.success is False
    assert result.forbidden is True
    assert result.value is None


@pytest.mark.unit
def test_never_commits_since_nothing_was_staged() -> None:
    nutrition = a_recorded_nutrition()
    uow = FakeUnitOfWork(entries=FakeNutritionRepository({nutrition.id: nutrition}))
    handler = GetNutritionHandler(uow=uow)

    handler.handle(GetNutritionQuery(nutrition_id=nutrition.id, requester_id=nutrition.user_id))

    assert uow.committed is False


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork(entries=FakeNutritionRepository(fail_on_get=True))
    handler = GetNutritionHandler(uow=uow)

    result = handler.handle(
        GetNutritionQuery(nutrition_id=NutritionId.generate(), requester_id=UserId.generate())
    )

    assert result.success is False
