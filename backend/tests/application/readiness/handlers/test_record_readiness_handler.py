"""Tests for
app/application/readiness/handlers/record_readiness_handler.py."""

from datetime import date, timedelta

import pytest

from app.application.readiness.commands.record_readiness import RecordReadinessCommand
from app.application.readiness.handlers.record_readiness_handler import RecordReadinessHandler
from app.domain.readiness.events import ReadinessRecorded
from app.domain.readiness.value_objects import EnergyLevel, ReadinessDate, SleepDuration
from app.domain.user.identifiers import UserId
from tests.application.readiness.factories import (
    FakeReadinessRepository,
    FakeUnitOfWork,
    FakeUserRepository,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_fixed_clock,
    a_registered_user,
)


def _a_command_for(user_id: UserId) -> RecordReadinessCommand:
    return RecordReadinessCommand(
        user_id=user_id,
        readiness_date=ReadinessDate(date(2026, 1, 1)),
        energy_level=EnergyLevel(6),
    )


@pytest.mark.unit
def test_records_a_new_readiness_check_in_and_returns_its_id() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    handler = RecordReadinessHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(_a_command_for(user.id))

    assert result.success is True
    assert result.value is not None
    stored = uow.entries.get(result.value)
    assert stored is not None
    assert stored.energy_level == EnergyLevel(6)


@pytest.mark.unit
def test_commits_the_unit_of_work() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    handler = RecordReadinessHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    handler.handle(_a_command_for(user.id))

    assert uow.committed is True
    assert uow.rolled_back is False


@pytest.mark.unit
def test_dispatches_readiness_recorded_after_commit() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    dispatcher = RecordingDispatcher()
    handler = RecordReadinessHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_a_command_for(user.id))

    assert len(dispatcher.dispatched) == 1
    event = dispatcher.dispatched[0]
    assert isinstance(event, ReadinessRecorded)
    assert event.readiness_id == result.value


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    user = a_registered_user()
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(users=FakeUserRepository({user.id: user}), call_order=call_order)
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = RecordReadinessHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(_a_command_for(user.id))

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_surfaces_a_sleep_warning_for_short_sleep_duration() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    handler = RecordReadinessHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )
    command = RecordReadinessCommand(
        user_id=user.id,
        readiness_date=ReadinessDate(date(2026, 1, 1)),
        sleep_duration=SleepDuration(timedelta(hours=4)),
    )

    result = handler.handle(command)

    assert result.success is True
    assert isinstance(result.warnings, tuple)
    assert any("sleep" in warning.lower() for warning in result.warnings)


@pytest.mark.unit
def test_a_missing_user_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = RecordReadinessHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_a_command_for(UserId.generate()))

    assert result.success is False
    assert "not found" in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_readiness_repository_add_failure_is_reported_as_a_failed_result() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(
        users=FakeUserRepository({user.id: user}),
        entries=FakeReadinessRepository(fail_on_add=True),
    )
    handler = RecordReadinessHandler(
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
    handler = RecordReadinessHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_a_command_for(user.id))

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_user_repository_get_failure_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork(users=FakeUserRepository(fail_on_get=True))
    handler = RecordReadinessHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(_a_command_for(UserId.generate()))

    assert result.success is False


@pytest.mark.unit
def test_generates_a_distinct_readiness_id_each_call() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    handler = RecordReadinessHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    first = handler.handle(_a_command_for(user.id))
    second = handler.handle(_a_command_for(user.id))

    assert first.value != second.value
