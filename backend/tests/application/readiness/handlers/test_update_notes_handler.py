"""Tests for app/application/readiness/handlers/update_notes_handler.py."""

import pytest

from app.application.readiness.commands.update_notes import UpdateNotesCommand
from app.application.readiness.handlers.update_notes_handler import UpdateNotesHandler
from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.value_objects import RecoveryNotes
from tests.application.readiness.factories import (
    FakeReadinessRepository,
    FakeUnitOfWork,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_fixed_clock,
    a_recorded_readiness,
)


@pytest.mark.unit
def test_replaces_notes_and_returns_the_readiness_id() -> None:
    readiness = a_recorded_readiness()
    uow = FakeUnitOfWork(entries=FakeReadinessRepository({readiness.id: readiness}))
    handler = UpdateNotesHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    result = handler.handle(
        UpdateNotesCommand(readiness_id=readiness.id, notes=RecoveryNotes("felt sluggish"))
    )

    assert result.success is True
    assert result.value == readiness.id
    assert readiness.notes == RecoveryNotes("felt sluggish")


@pytest.mark.unit
def test_commits_and_dispatches_recovery_notes_updated_after_commit() -> None:
    readiness = a_recorded_readiness()
    uow = FakeUnitOfWork(entries=FakeReadinessRepository({readiness.id: readiness}))
    dispatcher = RecordingDispatcher()
    handler = UpdateNotesHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(UpdateNotesCommand(readiness_id=readiness.id, notes=RecoveryNotes("note")))

    assert uow.committed is True
    kinds = {type(event).__name__ for event in dispatcher.dispatched}
    assert "RecoveryNotesUpdated" in kinds


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    readiness = a_recorded_readiness()
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(
        entries=FakeReadinessRepository({readiness.id: readiness}), call_order=call_order
    )
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = UpdateNotesHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(UpdateNotesCommand(readiness_id=readiness.id, notes=RecoveryNotes("note")))

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_does_not_evaluate_the_rule_engine_result_has_no_warnings() -> None:
    """No `ReadinessRuleEngine` evaluation here — see the handler's own
    module docstring for why notes are not rule-relevant.
    """
    readiness = a_recorded_readiness()
    uow = FakeUnitOfWork(entries=FakeReadinessRepository({readiness.id: readiness}))
    handler = UpdateNotesHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    result = handler.handle(
        UpdateNotesCommand(readiness_id=readiness.id, notes=RecoveryNotes("note"))
    )

    assert result.success is True
    assert result.warnings == ()


@pytest.mark.unit
def test_a_missing_readiness_check_in_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = UpdateNotesHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())
    missing_id = ReadinessId.generate()

    result = handler.handle(
        UpdateNotesCommand(readiness_id=missing_id, notes=RecoveryNotes("note"))
    )

    assert result.success is False
    assert str(missing_id) in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork(entries=FakeReadinessRepository(fail_on_get=True))
    dispatcher = RecordingDispatcher()
    handler = UpdateNotesHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        UpdateNotesCommand(readiness_id=ReadinessId.generate(), notes=RecoveryNotes("note"))
    )

    assert result.success is False
    assert uow.rolled_back is True


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    readiness = a_recorded_readiness()
    uow = FakeUnitOfWork(
        entries=FakeReadinessRepository({readiness.id: readiness}), fail_on_commit=True
    )
    dispatcher = RecordingDispatcher()
    handler = UpdateNotesHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        UpdateNotesCommand(readiness_id=readiness.id, notes=RecoveryNotes("note"))
    )

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []
