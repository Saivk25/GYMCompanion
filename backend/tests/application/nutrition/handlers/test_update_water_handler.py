"""Tests for app/application/nutrition/handlers/update_water_handler.py."""

import pytest

from app.application.nutrition.commands.update_water import UpdateWaterCommand
from app.application.nutrition.handlers.update_water_handler import UpdateWaterHandler
from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.value_objects import WaterIntake
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
def test_replaces_water_intake_and_returns_the_nutrition_id() -> None:
    nutrition = a_recorded_nutrition()
    uow = FakeUnitOfWork(entries=FakeNutritionRepository({nutrition.id: nutrition}))
    handler = UpdateWaterHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    result = handler.handle(
        UpdateWaterCommand(nutrition_id=nutrition.id, water_intake=WaterIntake(2000.0))
    )

    assert result.success is True
    assert result.value == nutrition.id
    assert nutrition.water_intake == WaterIntake(2000.0)


@pytest.mark.unit
def test_commits_and_dispatches_water_updated_after_commit() -> None:
    nutrition = a_recorded_nutrition()
    uow = FakeUnitOfWork(entries=FakeNutritionRepository({nutrition.id: nutrition}))
    dispatcher = RecordingDispatcher()
    handler = UpdateWaterHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(UpdateWaterCommand(nutrition_id=nutrition.id, water_intake=WaterIntake(2000.0)))

    assert uow.committed is True
    kinds = {type(event).__name__ for event in dispatcher.dispatched}
    assert "WaterUpdated" in kinds


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    nutrition = a_recorded_nutrition()
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(
        entries=FakeNutritionRepository({nutrition.id: nutrition}), call_order=call_order
    )
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = UpdateWaterHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(UpdateWaterCommand(nutrition_id=nutrition.id, water_intake=WaterIntake(2000.0)))

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_surfaces_hydration_warning_for_low_water_intake() -> None:
    nutrition = a_recorded_nutrition()
    uow = FakeUnitOfWork(entries=FakeNutritionRepository({nutrition.id: nutrition}))
    handler = UpdateWaterHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    result = handler.handle(
        UpdateWaterCommand(nutrition_id=nutrition.id, water_intake=WaterIntake(500.0))
    )

    assert result.success is True
    assert any("water" in warning.lower() for warning in result.warnings)


@pytest.mark.unit
def test_reports_no_warnings_for_water_intake_within_range() -> None:
    nutrition = a_recorded_nutrition()
    uow = FakeUnitOfWork(entries=FakeNutritionRepository({nutrition.id: nutrition}))
    handler = UpdateWaterHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    result = handler.handle(
        UpdateWaterCommand(nutrition_id=nutrition.id, water_intake=WaterIntake(2500.0))
    )

    assert result.success is True
    assert result.warnings == ()


@pytest.mark.unit
def test_a_missing_nutrition_entry_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = UpdateWaterHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())
    missing_id = NutritionId.generate()

    result = handler.handle(
        UpdateWaterCommand(nutrition_id=missing_id, water_intake=WaterIntake(2000.0))
    )

    assert result.success is False
    assert str(missing_id) in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork(entries=FakeNutritionRepository(fail_on_get=True))
    dispatcher = RecordingDispatcher()
    handler = UpdateWaterHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        UpdateWaterCommand(nutrition_id=NutritionId.generate(), water_intake=WaterIntake(2000.0))
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
    handler = UpdateWaterHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        UpdateWaterCommand(nutrition_id=nutrition.id, water_intake=WaterIntake(2000.0))
    )

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []
