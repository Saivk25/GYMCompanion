"""Tests for app/domain/workout/workout.py."""

from datetime import date, datetime, timedelta, timezone

import pytest

from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.user.identifiers import UserId
from app.domain.workout.enums import WorkoutStatus
from app.domain.workout.events import (
    WorkoutCancelled,
    WorkoutCompleted,
    WorkoutPlanned,
    WorkoutStarted,
)
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.value_objects import (
    WorkoutDate,
    WorkoutDuration,
    WorkoutGoal,
    WorkoutName,
    WorkoutNotes,
)
from app.domain.workout.workout import Workout
from tests.domain.workout.factories import a_fixed_clock, a_planned_workout

# --- plan() ---


@pytest.mark.unit
def test_plan_starts_in_the_planned_state() -> None:
    workout = a_planned_workout()
    assert workout.status == WorkoutStatus.PLANNED


@pytest.mark.unit
def test_plan_stamps_planned_at_from_the_clock() -> None:
    clock = a_fixed_clock()
    workout = Workout.plan(
        workout_id=WorkoutId.generate(),
        user_id=UserId.generate(),
        name=WorkoutName("Push Day"),
        planned_date=WorkoutDate(date(2026, 1, 1)),
        clock=clock,
    )
    assert workout.planned_at == clock.now()


@pytest.mark.unit
def test_plan_exposes_the_fields_it_was_given() -> None:
    workout_id = WorkoutId.generate()
    user_id = UserId.generate()
    workout = Workout.plan(
        workout_id=workout_id,
        user_id=user_id,
        name=WorkoutName("Push Day"),
        planned_date=WorkoutDate(date(2026, 1, 1)),
        goal=WorkoutGoal("upper body strength"),
        notes=WorkoutNotes("Focus on form"),
        clock=a_fixed_clock(),
    )
    assert workout.id == workout_id
    assert workout.user_id == user_id
    assert workout.name == WorkoutName("Push Day")
    assert workout.planned_date == WorkoutDate(date(2026, 1, 1))
    assert workout.goal == WorkoutGoal("upper body strength")
    assert workout.notes == WorkoutNotes("Focus on form")


@pytest.mark.unit
def test_plan_starts_with_no_duration_and_no_timestamps() -> None:
    workout = a_planned_workout()
    assert workout.duration is None
    assert workout.started_at is None
    assert workout.completed_at is None
    assert workout.cancelled_at is None


@pytest.mark.unit
def test_plan_starts_with_no_goal_or_notes_by_default() -> None:
    workout = a_planned_workout()
    assert workout.goal is None
    assert workout.notes is None


@pytest.mark.unit
def test_plan_records_a_workout_planned_event() -> None:
    clock = a_fixed_clock()
    workout_id = WorkoutId.generate()
    user_id = UserId.generate()
    workout = Workout.plan(
        workout_id=workout_id,
        user_id=user_id,
        name=WorkoutName("Push Day"),
        planned_date=WorkoutDate(date(2026, 1, 1)),
        clock=clock,
    )

    events = workout.pull_domain_events()

    assert len(events) == 1
    assert isinstance(events[0], WorkoutPlanned)
    assert events[0].workout_id == workout_id
    assert events[0].user_id == user_id
    assert events[0].name == WorkoutName("Push Day")
    assert events[0].planned_date == WorkoutDate(date(2026, 1, 1))
    assert events[0].occurred_at == clock.now()


@pytest.mark.unit
def test_plan_generates_a_distinct_workout_each_time() -> None:
    assert a_planned_workout().id != a_planned_workout().id


# --- update_goal() / update_notes() ---


@pytest.mark.unit
def test_update_goal_replaces_the_goal_without_an_event() -> None:
    workout = a_planned_workout()
    workout.pull_domain_events()  # drain WorkoutPlanned from setup

    workout.update_goal(WorkoutGoal("leg day"))

    assert workout.goal == WorkoutGoal("leg day")
    assert workout.pull_domain_events() == []


@pytest.mark.unit
def test_update_notes_replaces_the_notes_without_an_event() -> None:
    workout = a_planned_workout()
    workout.pull_domain_events()  # drain WorkoutPlanned from setup

    workout.update_notes(WorkoutNotes("Felt strong today"))

    assert workout.notes == WorkoutNotes("Felt strong today")
    assert workout.pull_domain_events() == []


@pytest.mark.unit
def test_update_goal_is_rejected_after_completion() -> None:
    workout = a_planned_workout()
    clock = a_fixed_clock()
    workout.start(clock=clock)
    workout.complete(duration=WorkoutDuration(timedelta(minutes=45)), clock=clock)

    with pytest.raises(DomainInvariantViolationError, match="cannot modify a workout"):
        workout.update_goal(WorkoutGoal("leg day"))


@pytest.mark.unit
def test_update_notes_is_rejected_after_cancellation() -> None:
    workout = a_planned_workout()
    workout.cancel(clock=a_fixed_clock())

    with pytest.raises(DomainInvariantViolationError, match="cannot modify a workout"):
        workout.update_notes(WorkoutNotes("too late"))


# --- start() ---


@pytest.mark.unit
def test_start_moves_planned_to_in_progress() -> None:
    workout = a_planned_workout()
    workout.start(clock=a_fixed_clock())
    assert workout.status == WorkoutStatus.IN_PROGRESS


@pytest.mark.unit
def test_start_stamps_started_at_from_the_clock() -> None:
    workout = a_planned_workout()
    clock = a_fixed_clock()
    workout.start(clock=clock)
    assert workout.started_at == clock.now()


@pytest.mark.unit
def test_start_records_a_workout_started_event() -> None:
    workout = a_planned_workout()
    workout.pull_domain_events()  # drain WorkoutPlanned from setup
    clock = a_fixed_clock()

    workout.start(clock=clock)

    events = workout.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], WorkoutStarted)
    assert events[0].workout_id == workout.id
    assert events[0].user_id == workout.user_id
    assert events[0].occurred_at == clock.now()


@pytest.mark.unit
def test_cannot_start_a_cancelled_workout() -> None:
    workout = a_planned_workout()
    workout.cancel(clock=a_fixed_clock())
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        workout.start(clock=a_fixed_clock())


@pytest.mark.unit
def test_cannot_start_twice() -> None:
    workout = a_planned_workout()
    workout.start(clock=a_fixed_clock())
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        workout.start(clock=a_fixed_clock())


@pytest.mark.unit
def test_cannot_start_a_completed_workout() -> None:
    workout = a_planned_workout()
    clock = a_fixed_clock()
    workout.start(clock=clock)
    workout.complete(duration=WorkoutDuration(timedelta(minutes=45)), clock=clock)
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        workout.start(clock=clock)


# --- complete() ---


@pytest.mark.unit
def test_complete_moves_in_progress_to_completed() -> None:
    workout = a_planned_workout()
    clock = a_fixed_clock()
    workout.start(clock=clock)
    workout.complete(duration=WorkoutDuration(timedelta(minutes=45)), clock=clock)
    assert workout.status == WorkoutStatus.COMPLETED


@pytest.mark.unit
def test_complete_stores_the_duration_and_stamps_completed_at() -> None:
    workout = a_planned_workout()
    clock = a_fixed_clock()
    workout.start(clock=clock)
    duration = WorkoutDuration(timedelta(minutes=45))

    workout.complete(duration=duration, clock=clock)

    assert workout.duration == duration
    assert workout.completed_at == clock.now()


@pytest.mark.unit
def test_complete_records_a_workout_completed_event() -> None:
    workout = a_planned_workout()
    clock = a_fixed_clock()
    workout.start(clock=clock)
    workout.pull_domain_events()  # drain WorkoutPlanned + WorkoutStarted
    duration = WorkoutDuration(timedelta(minutes=45))

    workout.complete(duration=duration, clock=clock)

    events = workout.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], WorkoutCompleted)
    assert events[0].workout_id == workout.id
    assert events[0].user_id == workout.user_id
    assert events[0].duration == duration
    assert events[0].occurred_at == clock.now()


@pytest.mark.unit
def test_cannot_complete_before_starting() -> None:
    workout = a_planned_workout()
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        workout.complete(duration=WorkoutDuration(timedelta(minutes=45)), clock=a_fixed_clock())


@pytest.mark.unit
def test_cannot_complete_twice() -> None:
    workout = a_planned_workout()
    clock = a_fixed_clock()
    workout.start(clock=clock)
    workout.complete(duration=WorkoutDuration(timedelta(minutes=45)), clock=clock)
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        workout.complete(duration=WorkoutDuration(timedelta(minutes=30)), clock=clock)


@pytest.mark.unit
def test_cannot_complete_a_cancelled_workout() -> None:
    workout = a_planned_workout()
    workout.cancel(clock=a_fixed_clock())
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        workout.complete(duration=WorkoutDuration(timedelta(minutes=45)), clock=a_fixed_clock())


# --- cancel() ---


@pytest.mark.unit
def test_cancel_moves_planned_to_cancelled() -> None:
    workout = a_planned_workout()
    workout.cancel(clock=a_fixed_clock())
    assert workout.status == WorkoutStatus.CANCELLED


@pytest.mark.unit
def test_cancel_moves_in_progress_to_cancelled() -> None:
    workout = a_planned_workout()
    clock = a_fixed_clock()
    workout.start(clock=clock)
    workout.cancel(clock=clock)
    assert workout.status == WorkoutStatus.CANCELLED


@pytest.mark.unit
def test_cancel_stamps_cancelled_at_from_the_clock() -> None:
    workout = a_planned_workout()
    clock = a_fixed_clock()
    workout.cancel(clock=clock)
    assert workout.cancelled_at == clock.now()


@pytest.mark.unit
def test_cancel_records_a_workout_cancelled_event() -> None:
    workout = a_planned_workout()
    workout.pull_domain_events()  # drain WorkoutPlanned from setup
    clock = a_fixed_clock()

    workout.cancel(clock=clock)

    events = workout.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], WorkoutCancelled)
    assert events[0].workout_id == workout.id
    assert events[0].user_id == workout.user_id
    assert events[0].occurred_at == clock.now()


@pytest.mark.unit
def test_cannot_cancel_after_completion() -> None:
    workout = a_planned_workout()
    clock = a_fixed_clock()
    workout.start(clock=clock)
    workout.complete(duration=WorkoutDuration(timedelta(minutes=45)), clock=clock)
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        workout.cancel(clock=clock)


@pytest.mark.unit
def test_cannot_cancel_a_cancelled_workout() -> None:
    workout = a_planned_workout()
    workout.cancel(clock=a_fixed_clock())
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        workout.cancel(clock=a_fixed_clock())


# --- full lifecycle ---


@pytest.mark.unit
def test_full_happy_path_lifecycle() -> None:
    workout = a_planned_workout()
    clock = a_fixed_clock()

    workout.start(clock=clock)
    workout.complete(duration=WorkoutDuration(timedelta(minutes=45)), clock=clock)

    assert workout.status == WorkoutStatus.COMPLETED
    events = workout.pull_domain_events()
    assert [type(event) for event in events] == [
        WorkoutPlanned,
        WorkoutStarted,
        WorkoutCompleted,
    ]


# --- __init__ construction (repository rehydration path) ---


@pytest.mark.unit
def test_constructor_rejects_a_naive_planned_at() -> None:
    with pytest.raises(DomainInvariantViolationError, match="timezone-aware"):
        Workout(
            WorkoutId.generate(),
            user_id=UserId.generate(),
            name=WorkoutName("Push Day"),
            planned_date=WorkoutDate(date(2026, 1, 1)),
            planned_at=datetime(2026, 1, 1),  # deliberately naive
        )


@pytest.mark.unit
def test_constructor_rehydrates_an_existing_workout_without_raising_an_event() -> None:
    """The path a repository uses to reconstruct a Workout already in
    storage — re-raising WorkoutPlanned here would be wrong."""
    workout = Workout(
        WorkoutId.generate(),
        user_id=UserId.generate(),
        name=WorkoutName("Push Day"),
        planned_date=WorkoutDate(date(2026, 1, 1)),
        planned_at=datetime.now(timezone.utc),
        status=WorkoutStatus.IN_PROGRESS,
        started_at=datetime.now(timezone.utc),
    )
    assert workout.pull_domain_events() == []
    assert workout.status == WorkoutStatus.IN_PROGRESS


@pytest.mark.unit
def test_constructor_accepts_explicit_optional_fields() -> None:
    duration = WorkoutDuration(timedelta(minutes=45))
    now = datetime.now(timezone.utc)
    workout = Workout(
        WorkoutId.generate(),
        user_id=UserId.generate(),
        name=WorkoutName("Push Day"),
        planned_date=WorkoutDate(date(2026, 1, 1)),
        planned_at=now,
        status=WorkoutStatus.COMPLETED,
        goal=WorkoutGoal("upper body strength"),
        notes=WorkoutNotes("Felt strong"),
        duration=duration,
        started_at=now,
        completed_at=now,
    )
    assert workout.goal == WorkoutGoal("upper body strength")
    assert workout.notes == WorkoutNotes("Felt strong")
    assert workout.duration == duration
    assert workout.started_at == now
    assert workout.completed_at == now
    assert workout.cancelled_at is None
