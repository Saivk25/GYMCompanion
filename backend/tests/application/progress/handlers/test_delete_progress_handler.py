"""Tests for app/application/progress/handlers/delete_progress_handler.py."""

import pytest

from app.application.progress.commands.delete_progress import DeleteProgressCommand
from app.application.progress.handlers.delete_progress_handler import DeleteProgressHandler
from app.domain.progress.identifiers import ProgressId
from app.domain.user.identifiers import UserId
from tests.application.progress.factories import (
    FakeProgressRepository,
    FakeUnitOfWork,
    RecordingDispatcher,
    a_recorded_progress,
)


@pytest.mark.unit
def test_removes_the_record_and_returns_its_id() -> None:
    progress = a_recorded_progress()
    records = FakeProgressRepository({progress.id: progress})
    uow = FakeUnitOfWork(records=records)
    handler = DeleteProgressHandler(uow=uow, dispatcher=RecordingDispatcher())

    result = handler.handle(
        DeleteProgressCommand(progress_id=progress.id, requester_id=progress.user_id)
    )

    assert result.success is True
    assert result.value == progress.id
    assert records.get(progress.id) is None
    assert progress in records.removed


@pytest.mark.unit
def test_commits_the_unit_of_work() -> None:
    progress = a_recorded_progress()
    uow = FakeUnitOfWork(records=FakeProgressRepository({progress.id: progress}))
    handler = DeleteProgressHandler(uow=uow, dispatcher=RecordingDispatcher())

    handler.handle(DeleteProgressCommand(progress_id=progress.id, requester_id=progress.user_id))

    assert uow.committed is True
    assert uow.rolled_back is False


@pytest.mark.unit
def test_dispatches_no_events_on_success() -> None:
    progress = a_recorded_progress()
    uow = FakeUnitOfWork(records=FakeProgressRepository({progress.id: progress}))
    dispatcher = RecordingDispatcher()
    handler = DeleteProgressHandler(uow=uow, dispatcher=dispatcher)

    handler.handle(DeleteProgressCommand(progress_id=progress.id, requester_id=progress.user_id))

    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_missing_progress_record_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = DeleteProgressHandler(uow=uow, dispatcher=dispatcher)
    missing_id = ProgressId.generate()

    result = handler.handle(
        DeleteProgressCommand(progress_id=missing_id, requester_id=UserId.generate())
    )

    assert result.success is False
    assert str(missing_id) in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork(records=FakeProgressRepository(fail_on_get=True))
    dispatcher = RecordingDispatcher()
    handler = DeleteProgressHandler(uow=uow, dispatcher=dispatcher)

    result = handler.handle(
        DeleteProgressCommand(progress_id=ProgressId.generate(), requester_id=UserId.generate())
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
    handler = DeleteProgressHandler(uow=uow, dispatcher=dispatcher)

    result = handler.handle(
        DeleteProgressCommand(progress_id=progress.id, requester_id=progress.user_id)
    )

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_non_owner_requester_is_denied_and_rolls_back() -> None:
    progress = a_recorded_progress()
    records = FakeProgressRepository({progress.id: progress})
    uow = FakeUnitOfWork(records=records)
    dispatcher = RecordingDispatcher()
    handler = DeleteProgressHandler(uow=uow, dispatcher=dispatcher)

    result = handler.handle(
        DeleteProgressCommand(progress_id=progress.id, requester_id=UserId.generate())
    )

    assert result.success is False
    assert result.forbidden is True
    assert result.value is None
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []
    assert records.get(progress.id) is progress
    assert progress not in records.removed
