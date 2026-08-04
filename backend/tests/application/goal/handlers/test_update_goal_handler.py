"""Tests for app/application/goal/handlers/update_goal_handler.py."""

from datetime import date

import pytest

from app.application.goal.commands.update_goal import UpdateGoalCommand
from app.application.goal.handlers.update_goal_handler import UpdateGoalHandler
from app.domain.goal.identifiers import GoalId
from app.domain.goal.value_objects import GoalName, TargetDate
from app.domain.shared_kernel.errors import DomainInvariantViolationError
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
def test_replaces_given_fields_and_returns_the_goal_id() -> None:
    goal = a_created_goal()
    uow = FakeUnitOfWork(goals=FakeGoalRepository({goal.id: goal}))
    handler = UpdateGoalHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    result = handler.handle(UpdateGoalCommand(goal_id=goal.id, name=GoalName("New Name")))

    assert result.success is True
    assert result.value == goal.id
    assert goal.name == GoalName("New Name")


@pytest.mark.unit
def test_leaves_fields_unset_in_the_command_unchanged() -> None:
    goal = a_created_goal()
    goal.update(target_date=TargetDate(date(2027, 1, 1)), clock=a_fixed_clock())
    goal.pull_domain_events()
    uow = FakeUnitOfWork(goals=FakeGoalRepository({goal.id: goal}))
    handler = UpdateGoalHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    handler.handle(UpdateGoalCommand(goal_id=goal.id, name=GoalName("New Name")))

    assert goal.target_date == TargetDate(date(2027, 1, 1))
    assert goal.name == GoalName("New Name")


@pytest.mark.unit
def test_commits_and_dispatches_goal_updated_after_commit() -> None:
    goal = a_created_goal()
    uow = FakeUnitOfWork(goals=FakeGoalRepository({goal.id: goal}))
    dispatcher = RecordingDispatcher()
    handler = UpdateGoalHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(UpdateGoalCommand(goal_id=goal.id, name=GoalName("New Name")))

    assert uow.committed is True
    kinds = {type(event).__name__ for event in dispatcher.dispatched}
    assert "GoalUpdated" in kinds


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    goal = a_created_goal()
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(goals=FakeGoalRepository({goal.id: goal}), call_order=call_order)
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = UpdateGoalHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(UpdateGoalCommand(goal_id=goal.id, name=GoalName("New Name")))

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_surfaces_a_target_date_warning_after_update() -> None:
    goal = a_created_goal()
    uow = FakeUnitOfWork(goals=FakeGoalRepository({goal.id: goal}))
    handler = UpdateGoalHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    result = handler.handle(
        UpdateGoalCommand(goal_id=goal.id, target_date=TargetDate(date(2025, 1, 1)))
    )

    assert result.success is True
    assert any("target date" in warning.lower() for warning in result.warnings)


@pytest.mark.unit
def test_a_missing_goal_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = UpdateGoalHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())
    missing_id = GoalId.generate()

    result = handler.handle(UpdateGoalCommand(goal_id=missing_id, name=GoalName("New Name")))

    assert result.success is False
    assert str(missing_id) in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork(goals=FakeGoalRepository(fail_on_get=True))
    dispatcher = RecordingDispatcher()
    handler = UpdateGoalHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(UpdateGoalCommand(goal_id=GoalId.generate(), name=GoalName("New Name")))

    assert result.success is False
    assert uow.rolled_back is True


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    goal = a_created_goal()
    uow = FakeUnitOfWork(goals=FakeGoalRepository({goal.id: goal}), fail_on_commit=True)
    dispatcher = RecordingDispatcher()
    handler = UpdateGoalHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(UpdateGoalCommand(goal_id=goal.id, name=GoalName("New Name")))

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_updating_a_completed_goal_raises_and_still_rolls_back() -> None:
    goal = a_created_goal()
    goal.complete(clock=a_fixed_clock())
    goal.pull_domain_events()
    uow = FakeUnitOfWork(goals=FakeGoalRepository({goal.id: goal}))
    dispatcher = RecordingDispatcher()
    handler = UpdateGoalHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    with pytest.raises(DomainInvariantViolationError, match="cannot update"):
        handler.handle(UpdateGoalCommand(goal_id=goal.id, name=GoalName("New Name")))

    assert dispatcher.dispatched == []
    assert uow.rolled_back is True
