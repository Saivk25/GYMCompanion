"""Tests for app/application/nutrition/handlers/list_nutrition_handler.py."""

import pytest

from app.application.nutrition.handlers.list_nutrition_handler import ListNutritionHandler
from app.application.nutrition.queries.list_nutrition import ListNutritionQuery
from app.domain.user.identifiers import UserId
from tests.application.nutrition.factories import (
    FakeNutritionRepository,
    FakeUnitOfWork,
    a_recorded_nutrition,
)


@pytest.mark.unit
def test_returns_every_entry_for_the_user_as_dtos() -> None:
    user_id = UserId.generate()
    mine_first = a_recorded_nutrition(user_id=user_id)
    mine_second = a_recorded_nutrition(user_id=user_id)
    someone_elses = a_recorded_nutrition()
    uow = FakeUnitOfWork(
        entries=FakeNutritionRepository(
            {
                mine_first.id: mine_first,
                mine_second.id: mine_second,
                someone_elses.id: someone_elses,
            }
        )
    )
    handler = ListNutritionHandler(uow=uow)

    result = handler.handle(ListNutritionQuery(user_id=user_id))

    assert result.success is True
    assert result.value is not None
    returned_ids = {dto.nutrition_id for dto in result.value}
    assert returned_ids == {mine_first.id, mine_second.id}


@pytest.mark.unit
def test_returns_an_empty_tuple_for_a_user_with_no_entries() -> None:
    uow = FakeUnitOfWork()
    handler = ListNutritionHandler(uow=uow)

    result = handler.handle(ListNutritionQuery(user_id=UserId.generate()))

    assert result.success is True
    assert result.value == ()


@pytest.mark.unit
def test_never_commits_since_nothing_was_staged() -> None:
    uow = FakeUnitOfWork()
    handler = ListNutritionHandler(uow=uow)

    handler.handle(ListNutritionQuery(user_id=UserId.generate()))

    assert uow.committed is False


@pytest.mark.unit
def test_a_repository_list_failure_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork(entries=FakeNutritionRepository(fail_on_list=True))
    handler = ListNutritionHandler(uow=uow)

    result = handler.handle(ListNutritionQuery(user_id=UserId.generate()))

    assert result.success is False
