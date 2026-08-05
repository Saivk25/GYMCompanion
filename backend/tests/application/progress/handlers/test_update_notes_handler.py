"""Tests for app/application/progress/handlers/update_notes_handler.py."""

import pytest

from app.application.progress.commands.update_notes import UpdateNotesCommand
from app.application.progress.handlers.update_notes_handler import UpdateNotesHandler
from app.domain.progress.identifiers import ProgressId
from app.domain.progress.value_objects import ProgressNotes
from app.domain.user.identifiers import UserId
from tests.application.progress.factories import (
    FakeProgressRepository,
    FakeUnitOfWork,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_fixed_clock,
    a_recorded_progress,
)


@pytest.mark.unit
def test_replaces_notes_and_returns_the_progress_id() -> None:
    progress = a_recorded_progress()
    uow = FakeUnitOfWork(records=FakeProgressRepository({progress.id: progress}))
    handler = UpdateNotesHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    result = handler.handle(
        UpdateNotesCommand(
            progress_id=progress.id,
            requester_id=progress.user_id,
            notes=ProgressNotes("measured fasted"),
        )
    )

    assert result.success is True
    assert result.value == progress.id
    assert progress.notes == ProgressNotes("measured fasted")


@pytest.mark.unit
def test_commits_and_dispatches_progress_notes_updated_after_commit() -> None:
    progress = a_recorded_progress()
    uow = FakeUnitOfWork(records=FakeProgressRepository({progress.id: progress}))
    dispatcher = RecordingDispatcher()
    handler = UpdateNotesHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(
        UpdateNotesCommand(
            progress_id=progress.id, requester_id=progress.user_id, notes=ProgressNotes("note")
        )
    )

    assert uow.committed is True
    kinds = {type(event).__name__ for event in dispatcher.dispatched}
    assert "ProgressNotesUpdated" in kinds


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    progress = a_recorded_progress()
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(
        records=FakeProgressRepository({progress.id: progress}), call_order=call_order
    )
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = UpdateNotesHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(
        UpdateNotesCommand(
            progress_id=progress.id, requester_id=progress.user_id, notes=ProgressNotes("note")
        )
    )

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_does_not_evaluate_the_rule_engine_result_has_no_warnings() -> None:
    """No `ProgressEvaluationRuleEngine` evaluation here — see the
    handler's own module docstring for why notes are not rule-relevant.
    """
    progress = a_recorded_progress()
    uow = FakeUnitOfWork(records=FakeProgressRepository({progress.id: progress}))
    handler = UpdateNotesHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    result = handler.handle(
        UpdateNotesCommand(
            progress_id=progress.id, requester_id=progress.user_id, notes=ProgressNotes("note")
        )
    )

    assert result.success is True
    assert result.warnings == ()


@pytest.mark.unit
def test_a_missing_progress_record_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = UpdateNotesHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())
    missing_id = ProgressId.generate()

    result = handler.handle(
        UpdateNotesCommand(
            progress_id=missing_id, requester_id=UserId.generate(), notes=ProgressNotes("note")
        )
    )

    assert result.success is False
    assert str(missing_id) in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork(records=FakeProgressRepository(fail_on_get=True))
    dispatcher = RecordingDispatcher()
    handler = UpdateNotesHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        UpdateNotesCommand(
            progress_id=ProgressId.generate(),
            requester_id=UserId.generate(),
            notes=ProgressNotes("note"),
        )
    )

    assert result.success is False
    assert uow.rolled_back is True


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    progress = a_recorded_progress()
    uow = FakeUnitOfWork(
        records=FakeProgressRepository({progress.id: progress}), fail_on_commit=True
    )
    dispatcher = RecordingDispatcher()
    handler = UpdateNotesHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        UpdateNotesCommand(
            progress_id=progress.id, requester_id=progress.user_id, notes=ProgressNotes("note")
        )
    )

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_non_owner_requester_is_denied_and_rolls_back() -> None:
    progress = a_recorded_progress()
    uow = FakeUnitOfWork(records=FakeProgressRepository({progress.id: progress}))
    dispatcher = RecordingDispatcher()
    handler = UpdateNotesHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        UpdateNotesCommand(
            progress_id=progress.id, requester_id=UserId.generate(), notes=ProgressNotes("note")
        )
    )

    assert result.success is False
    assert result.forbidden is True
    assert result.value is None
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []
