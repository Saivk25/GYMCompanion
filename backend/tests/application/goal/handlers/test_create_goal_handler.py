"""Tests for app/application/goal/handlers/create_goal_handler.py."""

from datetime import date

import pytest

from app.application.goal.commands.create_goal import CreateGoalCommand
from app.application.goal.handlers.create_goal_handler import CreateGoalHandler
from app.domain.goal.enums import GoalStatus, GoalType
from app.domain.goal.events import GoalCreated
from app.domain.goal.value_objects import GoalName, TargetDate, TargetWeight
from app.domain.user.identifiers import UserId
from tests.application.goal.factories import (
    FakeGoalRepository,
    FakeUnitOfWork,
    FakeUserRepository,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_fixed_clock,
    a_registered_user,
)


def _a_command_for(user_id: UserId) -> CreateGoalCommand:
    return CreateGoalCommand(
        user_id=user_id,
        goal_type=GoalType.LOSE_FAT,
        name=GoalName("Lose 5kg"),
        target_date=TargetDate(date(2026, 6, 1)),
    )


@pytest.mark.unit
def test_creates_a_new_active_goal_and_returns_its_id() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    handler = CreateGoalHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    result = handler.handle(_a_command_for(user.id))

    assert result.success is True
    assert result.value is not None
    stored = uow.goals.get(result.value)
    assert stored is not None
    assert stored.status == GoalStatus.ACTIVE
    assert stored.name == GoalName("Lose 5kg")


@pytest.mark.unit
def test_commits_the_unit_of_work() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    handler = CreateGoalHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    handler.handle(_a_command_for(user.id))

    assert uow.committed is True
    assert uow.rolled_back is False


@pytest.mark.unit
def test_dispatches_goal_created_after_commit() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    dispatcher = RecordingDispatcher()
    handler = CreateGoalHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_a_command_for(user.id))

    assert len(dispatcher.dispatched) == 1
    event = dispatcher.dispatched[0]
    assert isinstance(event, GoalCreated)
    assert event.goal_id == result.value


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    user = a_registered_user()
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(users=FakeUserRepository({user.id: user}), call_order=call_order)
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = CreateGoalHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(_a_command_for(user.id))

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_surfaces_a_target_date_warning_for_an_overdue_goal() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    handler = CreateGoalHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())
    command = CreateGoalCommand(
        user_id=user.id,
        goal_type=GoalType.LOSE_FAT,
        name=GoalName("Lose 5kg"),
        target_date=TargetDate(date(2025, 1, 1)),  # before the fixed clock's 2026-01-01
    )

    result = handler.handle(command)

    assert result.success is True
    assert isinstance(result.warnings, tuple)
    assert any("target date" in warning.lower() for warning in result.warnings)


@pytest.mark.unit
def test_no_warnings_for_a_comfortably_on_track_goal() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    handler = CreateGoalHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())
    command = CreateGoalCommand(
        user_id=user.id,
        goal_type=GoalType.LOSE_FAT,
        name=GoalName("Lose 5kg"),
        target_date=TargetDate(date(2027, 1, 1)),
        target_weight=TargetWeight(70.0),
    )

    result = handler.handle(command)

    assert result.success is True
    assert result.warnings == ()


@pytest.mark.unit
def test_a_missing_user_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = CreateGoalHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_a_command_for(UserId.generate()))

    assert result.success is False
    assert "not found" in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_goal_repository_add_failure_is_reported_as_a_failed_result() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(
        users=FakeUserRepository({user.id: user}),
        goals=FakeGoalRepository(fail_on_add=True),
    )
    handler = CreateGoalHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    result = handler.handle(_a_command_for(user.id))

    assert result.success is False
    assert "already exists" in result.errors[0]


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}), fail_on_commit=True)
    dispatcher = RecordingDispatcher()
    handler = CreateGoalHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_a_command_for(user.id))

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_user_repository_get_failure_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork(users=FakeUserRepository(fail_on_get=True))
    handler = CreateGoalHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    result = handler.handle(_a_command_for(UserId.generate()))

    assert result.success is False


@pytest.mark.unit
def test_generates_a_distinct_goal_id_each_call() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    handler = CreateGoalHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    first = handler.handle(_a_command_for(user.id))
    second = handler.handle(_a_command_for(user.id))

    assert first.value != second.value
