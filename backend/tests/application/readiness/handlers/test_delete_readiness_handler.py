"""Tests for
app/application/readiness/handlers/delete_readiness_handler.py."""

import pytest

from app.application.readiness.commands.delete_readiness import DeleteReadinessCommand
from app.application.readiness.handlers.delete_readiness_handler import DeleteReadinessHandler
from app.domain.readiness.identifiers import ReadinessId
from tests.application.readiness.factories import (
    FakeReadinessRepository,
    FakeUnitOfWork,
    RecordingDispatcher,
    a_recorded_readiness,
)


@pytest.mark.unit
def test_removes_the_check_in_and_returns_its_id() -> None:
    readiness = a_recorded_readiness()
    entries = FakeReadinessRepository({readiness.id: readiness})
    uow = FakeUnitOfWork(entries=entries)
    handler = DeleteReadinessHandler(uow=uow, dispatcher=RecordingDispatcher())

    result = handler.handle(DeleteReadinessCommand(readiness_id=readiness.id))

    assert result.success is True
    assert result.value == readiness.id
    assert entries.get(readiness.id) is None
    assert readiness in entries.removed


@pytest.mark.unit
def test_commits_the_unit_of_work() -> None:
    readiness = a_recorded_readiness()
    uow = FakeUnitOfWork(entries=FakeReadinessRepository({readiness.id: readiness}))
    handler = DeleteReadinessHandler(uow=uow, dispatcher=RecordingDispatcher())

    handler.handle(DeleteReadinessCommand(readiness_id=readiness.id))

    assert uow.committed is True
    assert uow.rolled_back is False


@pytest.mark.unit
def test_dispatches_no_events_on_success() -> None:
    readiness = a_recorded_readiness()
    uow = FakeUnitOfWork(entries=FakeReadinessRepository({readiness.id: readiness}))
    dispatcher = RecordingDispatcher()
    handler = DeleteReadinessHandler(uow=uow, dispatcher=dispatcher)

    handler.handle(DeleteReadinessCommand(readiness_id=readiness.id))

    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_missing_readiness_check_in_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = DeleteReadinessHandler(uow=uow, dispatcher=dispatcher)
    missing_id = ReadinessId.generate()

    result = handler.handle(DeleteReadinessCommand(readiness_id=missing_id))

    assert result.success is False
    assert str(missing_id) in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork(entries=FakeReadinessRepository(fail_on_get=True))
    dispatcher = RecordingDispatcher()
    handler = DeleteReadinessHandler(uow=uow, dispatcher=dispatcher)

    result = handler.handle(DeleteReadinessCommand(readiness_id=ReadinessId.generate()))

    assert result.success is False
    assert uow.rolled_back is True


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    readiness = a_recorded_readiness()
    uow = FakeUnitOfWork(
        entries=FakeReadinessRepository({readiness.id: readiness}), fail_on_commit=True
    )
    dispatcher = RecordingDispatcher()
    handler = DeleteReadinessHandler(uow=uow, dispatcher=dispatcher)

    result = handler.handle(DeleteReadinessCommand(readiness_id=readiness.id))

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []
