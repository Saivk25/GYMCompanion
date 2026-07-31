"""Tests for app/application/nutrition/handlers/update_nutrition_handler.py."""

import pytest

from app.application.nutrition.commands.update_nutrition import UpdateNutritionCommand
from app.application.nutrition.handlers.update_nutrition_handler import UpdateNutritionHandler
from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.value_objects import Calories, Fiber, Protein, WaterIntake
from tests.application.nutrition.factories import (
    FakeNutritionRepository,
    FakeUnitOfWork,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_fixed_clock,
    a_recorded_nutrition,
)


@pytest.mark.unit
def test_replaces_given_fields_and_returns_the_nutrition_id() -> None:
    nutrition = a_recorded_nutrition()
    uow = FakeUnitOfWork(entries=FakeNutritionRepository({nutrition.id: nutrition}))
    handler = UpdateNutritionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(
        UpdateNutritionCommand(
            nutrition_id=nutrition.id, calories=Calories(600.0), protein=Protein(40.0)
        )
    )

    assert result.success is True
    assert result.value == nutrition.id
    assert nutrition.calories == Calories(600.0)
    assert nutrition.protein == Protein(40.0)


@pytest.mark.unit
def test_leaves_fields_unset_in_the_command_unchanged() -> None:
    nutrition = a_recorded_nutrition()
    nutrition.update_nutrition(calories=Calories(500.0), fiber=Fiber(10.0), clock=a_fixed_clock())
    nutrition.pull_domain_events()
    uow = FakeUnitOfWork(entries=FakeNutritionRepository({nutrition.id: nutrition}))
    handler = UpdateNutritionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    handler.handle(UpdateNutritionCommand(nutrition_id=nutrition.id, protein=Protein(20.0)))

    assert nutrition.calories == Calories(500.0)
    assert nutrition.fiber == Fiber(10.0)
    assert nutrition.protein == Protein(20.0)


@pytest.mark.unit
def test_commits_and_dispatches_nutrition_updated_after_commit() -> None:
    nutrition = a_recorded_nutrition()
    uow = FakeUnitOfWork(entries=FakeNutritionRepository({nutrition.id: nutrition}))
    dispatcher = RecordingDispatcher()
    handler = UpdateNutritionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(UpdateNutritionCommand(nutrition_id=nutrition.id, calories=Calories(300.0)))

    assert uow.committed is True
    kinds = {type(event).__name__ for event in dispatcher.dispatched}
    assert "NutritionUpdated" in kinds


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    nutrition = a_recorded_nutrition()
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(
        entries=FakeNutritionRepository({nutrition.id: nutrition}), call_order=call_order
    )
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = UpdateNutritionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(UpdateNutritionCommand(nutrition_id=nutrition.id, calories=Calories(300.0)))

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_surfaces_hydration_warning_when_water_intake_is_already_low() -> None:
    nutrition = a_recorded_nutrition()
    nutrition.update_water(WaterIntake(500.0), clock=a_fixed_clock())
    nutrition.pull_domain_events()
    uow = FakeUnitOfWork(entries=FakeNutritionRepository({nutrition.id: nutrition}))
    handler = UpdateNutritionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(
        UpdateNutritionCommand(nutrition_id=nutrition.id, calories=Calories(300.0))
    )

    assert result.success is True
    assert any("water" in warning.lower() for warning in result.warnings)


@pytest.mark.unit
def test_a_missing_nutrition_entry_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = UpdateNutritionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())
    missing_id = NutritionId.generate()

    result = handler.handle(
        UpdateNutritionCommand(nutrition_id=missing_id, calories=Calories(300.0))
    )

    assert result.success is False
    assert str(missing_id) in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork(entries=FakeNutritionRepository(fail_on_get=True))
    dispatcher = RecordingDispatcher()
    handler = UpdateNutritionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        UpdateNutritionCommand(nutrition_id=NutritionId.generate(), calories=Calories(300.0))
    )

    assert result.success is False
    assert uow.rolled_back is True


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    nutrition = a_recorded_nutrition()
    uow = FakeUnitOfWork(
        entries=FakeNutritionRepository({nutrition.id: nutrition}), fail_on_commit=True
    )
    dispatcher = RecordingDispatcher()
    handler = UpdateNutritionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        UpdateNutritionCommand(nutrition_id=nutrition.id, calories=Calories(300.0))
    )

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []
