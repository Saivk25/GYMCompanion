"""Tests for app/domain/goal/goal.py."""

from datetime import date, datetime, timezone

import pytest

from app.domain.goal.enums import GoalStatus, GoalType
from app.domain.goal.events import GoalCancelled, GoalCompleted, GoalCreated, GoalUpdated
from app.domain.goal.goal import Goal
from app.domain.goal.identifiers import GoalId
from app.domain.goal.value_objects import (
    GoalDescription,
    GoalName,
    GoalNotes,
    Priority,
    TargetBodyFat,
    TargetDate,
    TargetStrength,
    TargetWeight,
)
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.user.identifiers import UserId
from tests.domain.goal.factories import a_created_goal, a_fixed_clock

# --- create() ---


@pytest.mark.unit
def test_create_starts_in_the_active_state() -> None:
    goal = a_created_goal()
    assert goal.status == GoalStatus.ACTIVE


@pytest.mark.unit
def test_create_stamps_created_at_from_the_clock() -> None:
    clock = a_fixed_clock()
    goal = Goal.create(
        goal_id=GoalId.generate(),
        user_id=UserId.generate(),
        goal_type=GoalType.LOSE_FAT,
        name=GoalName("Lose 5kg"),
        target_date=TargetDate(date(2026, 6, 1)),
        clock=clock,
    )
    assert goal.created_at == clock.now()


@pytest.mark.unit
def test_create_exposes_the_required_fields_it_was_given() -> None:
    goal_id = GoalId.generate()
    user_id = UserId.generate()
    name = GoalName("Lose 5kg")
    target_date = TargetDate(date(2026, 6, 1))
    goal = Goal.create(
        goal_id=goal_id,
        user_id=user_id,
        goal_type=GoalType.STRENGTH,
        name=name,
        target_date=target_date,
        clock=a_fixed_clock(),
    )
    assert goal.id == goal_id
    assert goal.user_id == user_id
    assert goal.goal_type is GoalType.STRENGTH
    assert goal.name == name
    assert goal.target_date == target_date


@pytest.mark.unit
def test_create_accepts_every_optional_field_at_once() -> None:
    goal = Goal.create(
        goal_id=GoalId.generate(),
        user_id=UserId.generate(),
        goal_type=GoalType.GAIN_MUSCLE,
        name=GoalName("Bulk up"),
        target_date=TargetDate(date(2026, 12, 1)),
        clock=a_fixed_clock(),
        description=GoalDescription("Add lean mass."),
        target_weight=TargetWeight(85.0),
        target_body_fat=TargetBodyFat(15.0),
        target_strength=TargetStrength(120.0),
        priority=Priority(1),
        notes=GoalNotes("Starting now."),
    )
    assert goal.description == GoalDescription("Add lean mass.")
    assert goal.target_weight == TargetWeight(85.0)
    assert goal.target_body_fat == TargetBodyFat(15.0)
    assert goal.target_strength == TargetStrength(120.0)
    assert goal.priority == Priority(1)
    assert goal.notes == GoalNotes("Starting now.")


@pytest.mark.unit
def test_create_defaults_every_optional_field_to_none_and_notes_to_empty() -> None:
    goal = a_created_goal()
    assert goal.description is None
    assert goal.target_weight is None
    assert goal.target_body_fat is None
    assert goal.target_strength is None
    assert goal.priority is None
    assert goal.notes == GoalNotes()


@pytest.mark.unit
def test_create_starts_with_no_updated_completed_or_cancelled_at() -> None:
    goal = a_created_goal()
    assert goal.updated_at is None
    assert goal.completed_at is None
    assert goal.cancelled_at is None


@pytest.mark.unit
def test_create_records_a_goal_created_event() -> None:
    clock = a_fixed_clock()
    goal_id = GoalId.generate()
    user_id = UserId.generate()
    name = GoalName("Lose 5kg")
    target_date = TargetDate(date(2026, 6, 1))
    goal = Goal.create(
        goal_id=goal_id,
        user_id=user_id,
        goal_type=GoalType.LOSE_FAT,
        name=name,
        target_date=target_date,
        clock=clock,
    )

    events = goal.pull_domain_events()

    assert len(events) == 1
    assert isinstance(events[0], GoalCreated)
    assert events[0].goal_id == goal_id
    assert events[0].user_id == user_id
    assert events[0].goal_type is GoalType.LOSE_FAT
    assert events[0].name == name
    assert events[0].target_date == target_date
    assert events[0].occurred_at == clock.now()


@pytest.mark.unit
def test_create_generates_a_distinct_goal_each_time() -> None:
    assert a_created_goal().id != a_created_goal().id


# --- rule: goal name required ---


@pytest.mark.unit
def test_goal_name_cannot_be_empty() -> None:
    with pytest.raises(DomainInvariantViolationError, match="goal name must not be empty"):
        GoalName("")


@pytest.mark.unit
def test_name_is_required_by_the_type_system() -> None:
    """`name` is a required, non-Optional constructor parameter — enforced
    statically by mypy for any real caller. Calling without it is a
    `TypeError` from Python itself, not a domain rule to test at runtime."""
    with pytest.raises(TypeError):
        Goal.create(  # type: ignore[call-arg]
            goal_id=GoalId.generate(),
            user_id=UserId.generate(),
            goal_type=GoalType.LOSE_FAT,
            target_date=TargetDate(date(2026, 6, 1)),
            clock=a_fixed_clock(),
        )


@pytest.mark.unit
def test_target_date_is_required_by_the_type_system() -> None:
    with pytest.raises(TypeError):
        Goal.create(  # type: ignore[call-arg]
            goal_id=GoalId.generate(),
            user_id=UserId.generate(),
            goal_type=GoalType.LOSE_FAT,
            name=GoalName("Lose 5kg"),
            clock=a_fixed_clock(),
        )


# --- update() ---


@pytest.mark.unit
def test_update_replaces_only_the_given_fields() -> None:
    goal = a_created_goal()
    original_target_date = goal.target_date

    goal.update(name=GoalName("New name"), clock=a_fixed_clock())

    assert goal.name == GoalName("New name")
    assert goal.target_date == original_target_date


@pytest.mark.unit
def test_update_can_replace_description() -> None:
    goal = a_created_goal()
    goal.update(description=GoalDescription("Updated."), clock=a_fixed_clock())
    assert goal.description == GoalDescription("Updated.")


@pytest.mark.unit
def test_update_can_replace_target_date() -> None:
    goal = a_created_goal()
    new_target_date = TargetDate(date(2027, 1, 1))
    goal.update(target_date=new_target_date, clock=a_fixed_clock())
    assert goal.target_date == new_target_date


@pytest.mark.unit
def test_update_can_replace_target_weight() -> None:
    goal = a_created_goal()
    goal.update(target_weight=TargetWeight(80.0), clock=a_fixed_clock())
    assert goal.target_weight == TargetWeight(80.0)


@pytest.mark.unit
def test_update_can_replace_target_body_fat() -> None:
    goal = a_created_goal()
    goal.update(target_body_fat=TargetBodyFat(12.0), clock=a_fixed_clock())
    assert goal.target_body_fat == TargetBodyFat(12.0)


@pytest.mark.unit
def test_update_can_replace_target_strength() -> None:
    goal = a_created_goal()
    goal.update(target_strength=TargetStrength(110.0), clock=a_fixed_clock())
    assert goal.target_strength == TargetStrength(110.0)


@pytest.mark.unit
def test_update_can_replace_priority() -> None:
    goal = a_created_goal()
    goal.update(priority=Priority(2), clock=a_fixed_clock())
    assert goal.priority == Priority(2)


@pytest.mark.unit
def test_update_can_replace_notes() -> None:
    goal = a_created_goal()
    goal.update(notes=GoalNotes("Progressing well."), clock=a_fixed_clock())
    assert goal.notes == GoalNotes("Progressing well.")


@pytest.mark.unit
def test_update_none_leaves_other_fields_unchanged() -> None:
    goal = a_created_goal()
    clock = a_fixed_clock()
    goal.update(target_weight=TargetWeight(80.0), priority=Priority(2), clock=clock)
    goal.update(priority=Priority(3), clock=clock)
    assert goal.target_weight == TargetWeight(80.0)
    assert goal.priority == Priority(3)


@pytest.mark.unit
def test_update_stamps_updated_at_from_the_clock() -> None:
    goal = a_created_goal()
    clock = a_fixed_clock()
    goal.update(name=GoalName("Renamed"), clock=clock)
    assert goal.updated_at == clock.now()


@pytest.mark.unit
def test_update_records_a_goal_updated_event_with_the_current_name() -> None:
    goal = a_created_goal()
    goal.pull_domain_events()  # drain GoalCreated from setup
    clock = a_fixed_clock()

    goal.update(name=GoalName("Renamed"), clock=clock)

    events = goal.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], GoalUpdated)
    assert events[0].goal_id == goal.id
    assert events[0].name == GoalName("Renamed")
    assert events[0].occurred_at == clock.now()


@pytest.mark.unit
def test_update_with_no_arguments_still_records_an_event_with_the_unchanged_name() -> None:
    goal = a_created_goal()
    goal.pull_domain_events()

    goal.update(clock=a_fixed_clock())

    events = goal.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], GoalUpdated)
    assert events[0].name == goal.name


# --- rule: cannot update completed/cancelled goals ---


@pytest.mark.unit
def test_cannot_update_a_completed_goal() -> None:
    goal = a_created_goal()
    goal.complete(clock=a_fixed_clock())
    with pytest.raises(DomainInvariantViolationError, match="cannot update a goal"):
        goal.update(name=GoalName("Renamed"), clock=a_fixed_clock())


@pytest.mark.unit
def test_cannot_update_a_cancelled_goal() -> None:
    goal = a_created_goal()
    goal.cancel(clock=a_fixed_clock())
    with pytest.raises(DomainInvariantViolationError, match="cannot update a goal"):
        goal.update(name=GoalName("Renamed"), clock=a_fixed_clock())


@pytest.mark.unit
def test_cannot_update_an_expired_goal() -> None:
    """No method ever sets a Goal to Expired — this exercises the guard via
    direct construction (the repository-rehydration path)."""
    goal = Goal(
        GoalId.generate(),
        user_id=UserId.generate(),
        goal_type=GoalType.LOSE_FAT,
        name=GoalName("Lose 5kg"),
        target_date=TargetDate(date(2026, 6, 1)),
        created_at=datetime.now(timezone.utc),
        status=GoalStatus.EXPIRED,
    )
    with pytest.raises(DomainInvariantViolationError, match="cannot update a goal"):
        goal.update(name=GoalName("Renamed"), clock=a_fixed_clock())


# --- complete() ---


@pytest.mark.unit
def test_complete_moves_active_to_completed() -> None:
    goal = a_created_goal()
    goal.complete(clock=a_fixed_clock())
    assert goal.status == GoalStatus.COMPLETED


@pytest.mark.unit
def test_complete_stamps_completed_at_from_the_clock() -> None:
    goal = a_created_goal()
    clock = a_fixed_clock()
    goal.complete(clock=clock)
    assert goal.completed_at == clock.now()


@pytest.mark.unit
def test_complete_records_a_goal_completed_event() -> None:
    goal = a_created_goal()
    goal.pull_domain_events()  # drain GoalCreated
    clock = a_fixed_clock()

    goal.complete(clock=clock)

    events = goal.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], GoalCompleted)
    assert events[0].goal_id == goal.id
    assert events[0].user_id == goal.user_id
    assert events[0].occurred_at == clock.now()


@pytest.mark.unit
def test_cannot_complete_a_goal_twice() -> None:
    goal = a_created_goal()
    goal.complete(clock=a_fixed_clock())
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        goal.complete(clock=a_fixed_clock())


# --- cancel() ---


@pytest.mark.unit
def test_cancel_moves_active_to_cancelled() -> None:
    goal = a_created_goal()
    goal.cancel(clock=a_fixed_clock())
    assert goal.status == GoalStatus.CANCELLED


@pytest.mark.unit
def test_cancel_stamps_cancelled_at_from_the_clock() -> None:
    goal = a_created_goal()
    clock = a_fixed_clock()
    goal.cancel(clock=clock)
    assert goal.cancelled_at == clock.now()


@pytest.mark.unit
def test_cancel_records_a_goal_cancelled_event() -> None:
    goal = a_created_goal()
    goal.pull_domain_events()  # drain GoalCreated
    clock = a_fixed_clock()

    goal.cancel(clock=clock)

    events = goal.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], GoalCancelled)
    assert events[0].goal_id == goal.id
    assert events[0].user_id == goal.user_id
    assert events[0].occurred_at == clock.now()


@pytest.mark.unit
def test_cannot_cancel_after_completion() -> None:
    goal = a_created_goal()
    goal.complete(clock=a_fixed_clock())
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        goal.cancel(clock=a_fixed_clock())


@pytest.mark.unit
def test_cannot_cancel_a_goal_twice() -> None:
    goal = a_created_goal()
    goal.cancel(clock=a_fixed_clock())
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        goal.cancel(clock=a_fixed_clock())


# --- __init__ construction (repository rehydration path) ---


@pytest.mark.unit
def test_constructor_rejects_a_naive_created_at() -> None:
    with pytest.raises(DomainInvariantViolationError, match="timezone-aware"):
        Goal(
            GoalId.generate(),
            user_id=UserId.generate(),
            goal_type=GoalType.LOSE_FAT,
            name=GoalName("Lose 5kg"),
            target_date=TargetDate(date(2026, 6, 1)),
            created_at=datetime(2026, 1, 1),  # deliberately naive
        )


@pytest.mark.unit
def test_constructor_rehydrates_an_existing_goal_without_raising_an_event() -> None:
    """The path a repository uses to reconstruct a Goal already in storage
    — re-raising GoalCreated here would be wrong."""
    goal = Goal(
        GoalId.generate(),
        user_id=UserId.generate(),
        goal_type=GoalType.LOSE_FAT,
        name=GoalName("Lose 5kg"),
        target_date=TargetDate(date(2026, 6, 1)),
        created_at=datetime.now(timezone.utc),
        status=GoalStatus.COMPLETED,
    )
    assert goal.pull_domain_events() == []
    assert goal.status == GoalStatus.COMPLETED


@pytest.mark.unit
def test_constructor_accepts_an_explicit_expired_status_with_no_event() -> None:
    """`GoalStatus.EXPIRED` is a legal rehydration-only value — no method on
    `Goal` ever transitions into it, but the constructor must accept it
    without raising."""
    goal = Goal(
        GoalId.generate(),
        user_id=UserId.generate(),
        goal_type=GoalType.LOSE_FAT,
        name=GoalName("Lose 5kg"),
        target_date=TargetDate(date(2026, 6, 1)),
        created_at=datetime.now(timezone.utc),
        status=GoalStatus.EXPIRED,
    )
    assert goal.status == GoalStatus.EXPIRED
    assert goal.pull_domain_events() == []


@pytest.mark.unit
def test_constructor_accepts_every_explicit_field() -> None:
    now = datetime.now(timezone.utc)
    goal = Goal(
        GoalId.generate(),
        user_id=UserId.generate(),
        goal_type=GoalType.ENDURANCE,
        name=GoalName("Run a marathon"),
        target_date=TargetDate(date(2026, 10, 1)),
        created_at=now,
        description=GoalDescription("Sub-4-hour marathon."),
        target_weight=TargetWeight(68.0),
        target_body_fat=TargetBodyFat(10.0),
        target_strength=TargetStrength(90.0),
        priority=Priority(2),
        notes=GoalNotes("Rehydrated."),
        status=GoalStatus.ACTIVE,
        updated_at=now,
        completed_at=None,
        cancelled_at=None,
    )
    assert goal.goal_type is GoalType.ENDURANCE
    assert goal.description == GoalDescription("Sub-4-hour marathon.")
    assert goal.target_weight == TargetWeight(68.0)
    assert goal.target_body_fat == TargetBodyFat(10.0)
    assert goal.target_strength == TargetStrength(90.0)
    assert goal.priority == Priority(2)
    assert goal.notes == GoalNotes("Rehydrated.")
    assert goal.updated_at == now
