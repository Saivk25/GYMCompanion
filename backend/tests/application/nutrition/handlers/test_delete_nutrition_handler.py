"""Tests for app/application/nutrition/handlers/delete_nutrition_handler.py."""

import pytest

from app.application.nutrition.commands.delete_nutrition import DeleteNutritionCommand
from app.application.nutrition.handlers.delete_nutrition_handler import DeleteNutritionHandler
from app.domain.nutrition.identifiers import NutritionId
from tests.application.nutrition.factories import (
    FakeNutritionRepository,
    FakeUnitOfWork,
    RecordingDispatcher,
    a_recorded_nutrition,
)


@pytest.mark.unit
def test_removes_the_entry_and_returns_its_id() -> None:
    nutrition = a_recorded_nutrition()
    entries = FakeNutritionRepository({nutrition.id: nutrition})
    uow = FakeUnitOfWork(entries=entries)
    handler = DeleteNutritionHandler(uow=uow, dispatcher=RecordingDispatcher())

    result = handler.handle(DeleteNutritionCommand(nutrition_id=nutrition.id))

    assert result.success is True
    assert result.value == nutrition.id
    assert entries.get(nutrition.id) is None
    assert nutrition in entries.removed


@pytest.mark.unit
def test_commits_the_unit_of_work() -> None:
    nutrition = a_recorded_nutrition()
    uow = FakeUnitOfWork(entries=FakeNutritionRepository({nutrition.id: nutrition}))
    handler = DeleteNutritionHandler(uow=uow, dispatcher=RecordingDispatcher())

    handler.handle(DeleteNutritionCommand(nutrition_id=nutrition.id))

    assert uow.committed is True
    assert uow.rolled_back is False


@pytest.mark.unit
def test_dispatches_no_events_on_success() -> None:
    nutrition = a_recorded_nutrition()
    uow = FakeUnitOfWork(entries=FakeNutritionRepository({nutrition.id: nutrition}))
    dispatcher = RecordingDispatcher()
    handler = DeleteNutritionHandler(uow=uow, dispatcher=dispatcher)

    handler.handle(DeleteNutritionCommand(nutrition_id=nutrition.id))

    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_missing_nutrition_entry_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = DeleteNutritionHandler(uow=uow, dispatcher=dispatcher)
    missing_id = NutritionId.generate()

    result = handler.handle(DeleteNutritionCommand(nutrition_id=missing_id))

    assert result.success is False
    assert str(missing_id) in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork(entries=FakeNutritionRepository(fail_on_get=True))
    dispatcher = RecordingDispatcher()
    handler = DeleteNutritionHandler(uow=uow, dispatcher=dispatcher)

    result = handler.handle(DeleteNutritionCommand(nutrition_id=NutritionId.generate()))

    assert result.success is False
    assert uow.rolled_back is True


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    nutrition = a_recorded_nutrition()
    uow = FakeUnitOfWork(
        entries=FakeNutritionRepository({nutrition.id: nutrition}), fail_on_commit=True
    )
    dispatcher = RecordingDispatcher()
    handler = DeleteNutritionHandler(uow=uow, dispatcher=dispatcher)

    result = handler.handle(DeleteNutritionCommand(nutrition_id=nutrition.id))

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []
