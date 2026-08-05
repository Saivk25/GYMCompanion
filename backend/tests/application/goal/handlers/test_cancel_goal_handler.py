"""Tests for app/application/goal/handlers/cancel_goal_handler.py."""

import pytest

from app.application.goal.commands.cancel_goal import CancelGoalCommand
from app.application.goal.handlers.cancel_goal_handler import CancelGoalHandler
from app.domain.goal.enums import GoalStatus
from app.domain.goal.identifiers import GoalId
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.user.identifiers import UserId
from tests.application.goal.factories import (
    FakeGoalRepository,
    FakeUnitOfWork,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_created_goal,
    a_fixed_clock,
)


@pytest.mark.unit
def test_cancels_the_goal_and_returns_its_id() -> None:
    goal = a_created_goal()
    uow = FakeUnitOfWork(goals=FakeGoalRepository({goal.id: goal}))
    handler = CancelGoalHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    result = handler.handle(CancelGoalCommand(goal_id=goal.id, requester_id=goal.user_id))

    assert result.success is True
    assert result.value == goal.id
    assert goal.status == GoalStatus.CANCELLED
    assert result.warnings == ()


@pytest.mark.unit
def test_commits_and_dispatches_after_commit() -> None:
    goal = a_created_goal()
    uow = FakeUnitOfWork(goals=FakeGoalRepository({goal.id: goal}))
    dispatcher = RecordingDispatcher()
    handler = CancelGoalHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(CancelGoalCommand(goal_id=goal.id, requester_id=goal.user_id))

    assert uow.committed is True
    assert len(dispatcher.dispatched) == 1


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    goal = a_created_goal()
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(goals=FakeGoalRepository({goal.id: goal}), call_order=call_order)
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = CancelGoalHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(CancelGoalCommand(goal_id=goal.id, requester_id=goal.user_id))

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_a_missing_goal_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = CancelGoalHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())
    missing_id = GoalId.generate()

    result = handler.handle(CancelGoalCommand(goal_id=missing_id, requester_id=UserId.generate()))

    assert result.success is False
    assert str(missing_id) in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork(goals=FakeGoalRepository(fail_on_get=True))
    dispatcher = RecordingDispatcher()
    handler = CancelGoalHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        CancelGoalCommand(goal_id=GoalId.generate(), requester_id=UserId.generate())
    )

    assert result.success is False
    assert uow.rolled_back is True


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    goal = a_created_goal()
    uow = FakeUnitOfWork(goals=FakeGoalRepository({goal.id: goal}), fail_on_commit=True)
    dispatcher = RecordingDispatcher()
    handler = CancelGoalHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(CancelGoalCommand(goal_id=goal.id, requester_id=goal.user_id))

    assert result.success is False
    assert uow.rolled_back is True


@pytest.mark.unit
def test_cancelling_a_completed_goal_raises_and_still_rolls_back() -> None:
    goal = a_created_goal()
    goal.complete(clock=a_fixed_clock())
    goal.pull_domain_events()
    uow = FakeUnitOfWork(goals=FakeGoalRepository({goal.id: goal}))
    dispatcher = RecordingDispatcher()
    handler = CancelGoalHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        handler.handle(CancelGoalCommand(goal_id=goal.id, requester_id=goal.user_id))

    assert dispatcher.dispatched == []
    assert uow.rolled_back is True


@pytest.mark.unit
def test_cancelling_an_already_cancelled_goal_raises() -> None:
    goal = a_created_goal()
    goal.cancel(clock=a_fixed_clock())
    goal.pull_domain_events()
    uow = FakeUnitOfWork(goals=FakeGoalRepository({goal.id: goal}))
    handler = CancelGoalHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        handler.handle(CancelGoalCommand(goal_id=goal.id, requester_id=goal.user_id))


@pytest.mark.unit
def test_a_non_owner_requester_is_denied_and_rolls_back() -> None:
    goal = a_created_goal()
    uow = FakeUnitOfWork(goals=FakeGoalRepository({goal.id: goal}))
    dispatcher = RecordingDispatcher()
    handler = CancelGoalHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(CancelGoalCommand(goal_id=goal.id, requester_id=UserId.generate()))

    assert result.success is False
    assert result.forbidden is True
    assert result.value is None
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []
