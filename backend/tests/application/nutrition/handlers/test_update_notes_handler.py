"""Tests for app/application/nutrition/handlers/update_notes_handler.py."""

import pytest

from app.application.nutrition.commands.update_notes import UpdateNutritionNotesCommand
from app.application.nutrition.handlers.update_notes_handler import UpdateNutritionNotesHandler
from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.value_objects import MealNotes
from app.domain.user.identifiers import UserId
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
def test_replaces_notes_and_returns_the_nutrition_id() -> None:
    nutrition = a_recorded_nutrition()
    uow = FakeUnitOfWork(entries=FakeNutritionRepository({nutrition.id: nutrition}))
    handler = UpdateNutritionNotesHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(
        UpdateNutritionNotesCommand(
            nutrition_id=nutrition.id, requester_id=nutrition.user_id, notes=MealNotes("ate out")
        )
    )

    assert result.success is True
    assert result.value == nutrition.id
    assert nutrition.notes == MealNotes("ate out")


@pytest.mark.unit
def test_commits_and_dispatches_meal_notes_updated_after_commit() -> None:
    nutrition = a_recorded_nutrition()
    uow = FakeUnitOfWork(entries=FakeNutritionRepository({nutrition.id: nutrition}))
    dispatcher = RecordingDispatcher()
    handler = UpdateNutritionNotesHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(
        UpdateNutritionNotesCommand(
            nutrition_id=nutrition.id, requester_id=nutrition.user_id, notes=MealNotes("note")
        )
    )

    assert uow.committed is True
    kinds = {type(event).__name__ for event in dispatcher.dispatched}
    assert "MealNotesUpdated" in kinds


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    nutrition = a_recorded_nutrition()
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(
        entries=FakeNutritionRepository({nutrition.id: nutrition}), call_order=call_order
    )
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = UpdateNutritionNotesHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(
        UpdateNutritionNotesCommand(
            nutrition_id=nutrition.id, requester_id=nutrition.user_id, notes=MealNotes("note")
        )
    )

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_does_not_evaluate_the_rule_engine_result_has_no_warnings() -> None:
    """No `NutritionRuleEngine` evaluation here — see the handler's own
    module docstring for why notes are not rule-relevant.
    """
    nutrition = a_recorded_nutrition()
    uow = FakeUnitOfWork(entries=FakeNutritionRepository({nutrition.id: nutrition}))
    handler = UpdateNutritionNotesHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(
        UpdateNutritionNotesCommand(
            nutrition_id=nutrition.id, requester_id=nutrition.user_id, notes=MealNotes("note")
        )
    )

    assert result.success is True
    assert result.warnings == ()


@pytest.mark.unit
def test_a_missing_nutrition_entry_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = UpdateNutritionNotesHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())
    missing_id = NutritionId.generate()

    result = handler.handle(
        UpdateNutritionNotesCommand(
            nutrition_id=missing_id, requester_id=UserId.generate(), notes=MealNotes("note")
        )
    )

    assert result.success is False
    assert str(missing_id) in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_requester_who_does_not_own_the_entry_is_forbidden_and_rolls_back() -> None:
    nutrition = a_recorded_nutrition()
    uow = FakeUnitOfWork(entries=FakeNutritionRepository({nutrition.id: nutrition}))
    dispatcher = RecordingDispatcher()
    handler = UpdateNutritionNotesHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        UpdateNutritionNotesCommand(
            nutrition_id=nutrition.id, requester_id=UserId.generate(), notes=MealNotes("note")
        )
    )

    assert result.success is False
    assert result.forbidden is True
    assert result.value is None
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork(entries=FakeNutritionRepository(fail_on_get=True))
    dispatcher = RecordingDispatcher()
    handler = UpdateNutritionNotesHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        UpdateNutritionNotesCommand(
            nutrition_id=NutritionId.generate(),
            requester_id=UserId.generate(),
            notes=MealNotes("note"),
        )
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
    handler = UpdateNutritionNotesHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        UpdateNutritionNotesCommand(
            nutrition_id=nutrition.id, requester_id=nutrition.user_id, notes=MealNotes("note")
        )
    )

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []
