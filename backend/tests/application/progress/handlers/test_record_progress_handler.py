"""Tests for app/application/progress/handlers/record_progress_handler.py."""

from datetime import date

import pytest

from app.application.progress.commands.record_progress import RecordProgressCommand
from app.application.progress.handlers.record_progress_handler import RecordProgressHandler
from app.domain.progress.enums import MeasurementUnit, ProgressSource
from app.domain.progress.events import ProgressRecorded
from app.domain.progress.value_objects import BodyWeight, ProgressDate
from app.domain.user.identifiers import UserId
from tests.application.progress.factories import (
    FakeProgressRepository,
    FakeUnitOfWork,
    FakeUserRepository,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_fixed_clock,
    a_recorded_progress,
    a_registered_user,
)


def _a_command_for(
    user_id: UserId, *, progress_date: date = date(2026, 1, 1)
) -> RecordProgressCommand:
    return RecordProgressCommand(
        user_id=user_id,
        progress_date=ProgressDate(progress_date),
        unit=MeasurementUnit.METRIC,
        source=ProgressSource.MANUAL,
        body_weight=BodyWeight(80.0),
    )


@pytest.mark.unit
def test_records_a_new_progress_check_in_and_returns_its_id() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    handler = RecordProgressHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(_a_command_for(user.id))

    assert result.success is True
    assert result.value is not None
    stored = uow.records.get(result.value)
    assert stored is not None
    assert stored.body_weight == BodyWeight(80.0)


@pytest.mark.unit
def test_commits_the_unit_of_work() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    handler = RecordProgressHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    handler.handle(_a_command_for(user.id))

    assert uow.committed is True
    assert uow.rolled_back is False


@pytest.mark.unit
def test_dispatches_progress_recorded_after_commit() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    dispatcher = RecordingDispatcher()
    handler = RecordProgressHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_a_command_for(user.id))

    assert len(dispatcher.dispatched) == 1
    event = dispatcher.dispatched[0]
    assert isinstance(event, ProgressRecorded)
    assert event.progress_id == result.value


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    user = a_registered_user()
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(users=FakeUserRepository({user.id: user}), call_order=call_order)
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = RecordProgressHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(_a_command_for(user.id))

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_surfaces_consistency_warning_for_a_first_ever_check_in() -> None:
    """`ConsistencyRule` fails (advisory) when fewer than 3 entries exist
    — a brand-new user's first check-in always triggers it."""
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    handler = RecordProgressHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(_a_command_for(user.id))

    assert result.success is True
    assert isinstance(result.warnings, tuple)
    assert any("log progress more regularly" in warning.lower() for warning in result.warnings)


@pytest.mark.unit
def test_evaluates_the_rule_engine_against_the_users_full_history_not_just_the_new_entry() -> None:
    """Two prior entries plus this one clears `ConsistencyRule`'s
    minimum-3 threshold — proof the engine sees `list_by_user()`'s full
    history, not just the just-recorded record."""
    user = a_registered_user()
    first = a_recorded_progress(user_id=user.id, progress_date=ProgressDate(date(2025, 12, 20)))
    second = a_recorded_progress(user_id=user.id, progress_date=ProgressDate(date(2025, 12, 27)))
    existing = FakeProgressRepository({first.id: first, second.id: second})
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}), records=existing)
    handler = RecordProgressHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(_a_command_for(user.id))

    assert result.success is True
    assert not any("log progress more regularly" in warning.lower() for warning in result.warnings)


@pytest.mark.unit
def test_a_missing_user_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = RecordProgressHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_a_command_for(UserId.generate()))

    assert result.success is False
    assert "not found" in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_progress_repository_add_failure_is_reported_as_a_failed_result() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(
        users=FakeUserRepository({user.id: user}),
        records=FakeProgressRepository(fail_on_add=True),
    )
    handler = RecordProgressHandler(
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
    handler = RecordProgressHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_a_command_for(user.id))

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_user_repository_get_failure_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork(users=FakeUserRepository(fail_on_get=True))
    handler = RecordProgressHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(_a_command_for(UserId.generate()))

    assert result.success is False


@pytest.mark.unit
def test_generates_a_distinct_progress_id_each_call() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    handler = RecordProgressHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    first = handler.handle(_a_command_for(user.id))
    second = handler.handle(_a_command_for(user.id, progress_date=date(2026, 1, 2)))

    assert first.value != second.value
