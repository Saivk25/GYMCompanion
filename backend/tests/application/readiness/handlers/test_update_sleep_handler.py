"""Tests for app/application/readiness/handlers/update_sleep_handler.py."""

from datetime import timedelta

import pytest

from app.application.readiness.commands.update_sleep import UpdateSleepCommand
from app.application.readiness.handlers.update_sleep_handler import UpdateSleepHandler
from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.value_objects import SleepDuration, SleepQuality
from app.domain.user.identifiers import UserId
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
def test_replaces_given_fields_and_returns_the_readiness_id() -> None:
    readiness = a_recorded_readiness()
    uow = FakeUnitOfWork(entries=FakeReadinessRepository({readiness.id: readiness}))
    handler = UpdateSleepHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    result = handler.handle(
        UpdateSleepCommand(
            readiness_id=readiness.id,
            requester_id=readiness.user_id,
            sleep_duration=SleepDuration(timedelta(hours=8)),
            sleep_quality=SleepQuality(9),
        )
    )

    assert result.success is True
    assert result.value == readiness.id
    assert readiness.sleep_duration == SleepDuration(timedelta(hours=8))
    assert readiness.sleep_quality == SleepQuality(9)


@pytest.mark.unit
def test_leaves_fields_unset_in_the_command_unchanged() -> None:
    readiness = a_recorded_readiness()
    readiness.update_sleep(
        sleep_duration=SleepDuration(timedelta(hours=8)),
        sleep_quality=SleepQuality(9),
        clock=a_fixed_clock(),
    )
    readiness.pull_domain_events()
    uow = FakeUnitOfWork(entries=FakeReadinessRepository({readiness.id: readiness}))
    handler = UpdateSleepHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    handler.handle(
        UpdateSleepCommand(
            readiness_id=readiness.id, requester_id=readiness.user_id, sleep_quality=SleepQuality(6)
        )
    )

    assert readiness.sleep_duration == SleepDuration(timedelta(hours=8))
    assert readiness.sleep_quality == SleepQuality(6)


@pytest.mark.unit
def test_commits_and_dispatches_sleep_updated_after_commit() -> None:
    readiness = a_recorded_readiness()
    uow = FakeUnitOfWork(entries=FakeReadinessRepository({readiness.id: readiness}))
    dispatcher = RecordingDispatcher()
    handler = UpdateSleepHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(
        UpdateSleepCommand(
            readiness_id=readiness.id, requester_id=readiness.user_id, sleep_quality=SleepQuality(7)
        )
    )

    assert uow.committed is True
    kinds = {type(event).__name__ for event in dispatcher.dispatched}
    assert "SleepUpdated" in kinds


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    readiness = a_recorded_readiness()
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(
        entries=FakeReadinessRepository({readiness.id: readiness}), call_order=call_order
    )
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = UpdateSleepHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(
        UpdateSleepCommand(
            readiness_id=readiness.id, requester_id=readiness.user_id, sleep_quality=SleepQuality(7)
        )
    )

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_surfaces_a_sleep_warning_for_short_sleep_duration() -> None:
    readiness = a_recorded_readiness()
    uow = FakeUnitOfWork(entries=FakeReadinessRepository({readiness.id: readiness}))
    handler = UpdateSleepHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    result = handler.handle(
        UpdateSleepCommand(
            readiness_id=readiness.id,
            requester_id=readiness.user_id,
            sleep_duration=SleepDuration(timedelta(hours=3)),
        )
    )

    assert result.success is True
    assert any("sleep" in warning.lower() for warning in result.warnings)


@pytest.mark.unit
def test_a_missing_readiness_check_in_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = UpdateSleepHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())
    missing_id = ReadinessId.generate()

    result = handler.handle(
        UpdateSleepCommand(
            readiness_id=missing_id, requester_id=UserId.generate(), sleep_quality=SleepQuality(7)
        )
    )

    assert result.success is False
    assert str(missing_id) in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork(entries=FakeReadinessRepository(fail_on_get=True))
    dispatcher = RecordingDispatcher()
    handler = UpdateSleepHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        UpdateSleepCommand(
            readiness_id=ReadinessId.generate(),
            requester_id=UserId.generate(),
            sleep_quality=SleepQuality(7),
        )
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
    handler = UpdateSleepHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        UpdateSleepCommand(
            readiness_id=readiness.id, requester_id=readiness.user_id, sleep_quality=SleepQuality(7)
        )
    )

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_non_owner_requester_is_denied_and_rolls_back() -> None:
    readiness = a_recorded_readiness()
    uow = FakeUnitOfWork(entries=FakeReadinessRepository({readiness.id: readiness}))
    dispatcher = RecordingDispatcher()
    handler = UpdateSleepHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        UpdateSleepCommand(
            readiness_id=readiness.id, requester_id=UserId.generate(), sleep_quality=SleepQuality(7)
        )
    )

    assert result.success is False
    assert result.forbidden is True
    assert result.value is None
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []
