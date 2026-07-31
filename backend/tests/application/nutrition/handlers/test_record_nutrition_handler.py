"""Tests for app/application/nutrition/handlers/record_nutrition_handler.py."""

from datetime import date

import pytest

from app.application.nutrition.commands.record_nutrition import RecordNutritionCommand
from app.application.nutrition.handlers.record_nutrition_handler import RecordNutritionHandler
from app.domain.nutrition.events import NutritionRecorded
from app.domain.nutrition.value_objects import Calories, NutritionDate, Protein, WaterIntake
from app.domain.user.identifiers import UserId
from tests.application.nutrition.factories import (
    FakeNutritionRepository,
    FakeUnitOfWork,
    FakeUserRepository,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_fixed_clock,
    a_registered_user,
)


def _a_command_for(user_id: UserId) -> RecordNutritionCommand:
    return RecordNutritionCommand(
        user_id=user_id,
        nutrition_date=NutritionDate(date(2026, 1, 1)),
        calories=Calories(500.0),
        protein=Protein(30.0),
    )


@pytest.mark.unit
def test_records_a_new_nutrition_entry_and_returns_its_id() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    handler = RecordNutritionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(_a_command_for(user.id))

    assert result.success is True
    assert result.value is not None
    stored = uow.entries.get(result.value)
    assert stored is not None
    assert stored.calories == Calories(500.0)


@pytest.mark.unit
def test_commits_the_unit_of_work() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    handler = RecordNutritionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    handler.handle(_a_command_for(user.id))

    assert uow.committed is True
    assert uow.rolled_back is False


@pytest.mark.unit
def test_dispatches_nutrition_recorded_after_commit() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    dispatcher = RecordingDispatcher()
    handler = RecordNutritionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_a_command_for(user.id))

    assert len(dispatcher.dispatched) == 1
    event = dispatcher.dispatched[0]
    assert isinstance(event, NutritionRecorded)
    assert event.nutrition_id == result.value


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    user = a_registered_user()
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(users=FakeUserRepository({user.id: user}), call_order=call_order)
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = RecordNutritionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(_a_command_for(user.id))

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_surfaces_hydration_warning_for_low_water_intake() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    handler = RecordNutritionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )
    command = RecordNutritionCommand(
        user_id=user.id,
        nutrition_date=NutritionDate(date(2026, 1, 1)),
        water_intake=WaterIntake(500.0),
    )

    result = handler.handle(command)

    assert result.success is True
    assert isinstance(result.warnings, tuple)
    assert any("water" in warning.lower() for warning in result.warnings)


@pytest.mark.unit
def test_a_missing_user_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = RecordNutritionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_a_command_for(UserId.generate()))

    assert result.success is False
    assert "not found" in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_nutrition_repository_add_failure_is_reported_as_a_failed_result() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(
        users=FakeUserRepository({user.id: user}),
        entries=FakeNutritionRepository(fail_on_add=True),
    )
    handler = RecordNutritionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(_a_command_for(user.id))

    assert result.success is False
    assert "already exists" in result.errors[0]


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}), fail_on_commit=True)
    dispatcher = RecordingDispatcher()
    handler = RecordNutritionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_a_command_for(user.id))

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_user_repository_get_failure_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork(users=FakeUserRepository(fail_on_get=True))
    handler = RecordNutritionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(_a_command_for(UserId.generate()))

    assert result.success is False


@pytest.mark.unit
def test_generates_a_distinct_nutrition_id_each_call() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    handler = RecordNutritionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    first = handler.handle(_a_command_for(user.id))
    second = handler.handle(_a_command_for(user.id))

    assert first.value != second.value
