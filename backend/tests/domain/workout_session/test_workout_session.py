"""Tests for app/domain/workout_session/workout_session.py."""

from datetime import date, datetime, timedelta, timezone

import pytest

from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout_session.enums import SessionStatus
from app.domain.workout_session.events import (
    WorkoutSessionAbandoned,
    WorkoutSessionCompleted,
    WorkoutSessionNotesUpdated,
    WorkoutSessionStarted,
)
from app.domain.workout_session.identifiers import WorkoutSessionId
from app.domain.workout_session.value_objects import (
    CompletionPercentage,
    SessionDate,
    SessionDuration,
    SessionNotes,
    SessionRating,
)
from app.domain.workout_session.workout_session import WorkoutSession
from tests.domain.workout_session.factories import a_fixed_clock, a_planned_session

# --- plan() ---


@pytest.mark.unit
def test_plan_starts_in_the_planned_state() -> None:
    session = a_planned_session()
    assert session.status == SessionStatus.PLANNED


@pytest.mark.unit
def test_plan_stamps_planned_at_from_the_clock() -> None:
    clock = a_fixed_clock()
    session = WorkoutSession.plan(
        session_id=WorkoutSessionId.generate(),
        workout_id=WorkoutId.generate(),
        user_id=UserId.generate(),
        session_date=SessionDate(date(2026, 1, 1)),
        clock=clock,
    )
    assert session.planned_at == clock.now()


@pytest.mark.unit
def test_plan_exposes_the_fields_it_was_given() -> None:
    session_id = WorkoutSessionId.generate()
    workout_id = WorkoutId.generate()
    user_id = UserId.generate()
    session = WorkoutSession.plan(
        session_id=session_id,
        workout_id=workout_id,
        user_id=user_id,
        session_date=SessionDate(date(2026, 1, 1)),
        clock=a_fixed_clock(),
    )
    assert session.id == session_id
    assert session.workout_id == workout_id
    assert session.user_id == user_id
    assert session.session_date == SessionDate(date(2026, 1, 1))


@pytest.mark.unit
def test_plan_defaults_to_empty_notes_and_no_duration_rating_or_completion() -> None:
    session = a_planned_session()
    assert session.notes == SessionNotes()
    assert session.duration is None
    assert session.completion_percentage is None
    assert session.rating is None


@pytest.mark.unit
def test_plan_starts_with_no_timestamps() -> None:
    session = a_planned_session()
    assert session.started_at is None
    assert session.completed_at is None
    assert session.abandoned_at is None


@pytest.mark.unit
def test_plan_raises_no_event() -> None:
    """Deliberate — see events.py's module docstring: this increment's
    task names four events starting from WorkoutSessionStarted, no
    creation event, unlike every other aggregate in this codebase."""
    session = a_planned_session()
    assert session.pull_domain_events() == []


@pytest.mark.unit
def test_plan_generates_a_distinct_session_each_time() -> None:
    assert a_planned_session().id != a_planned_session().id


# --- update_notes() ---


@pytest.mark.unit
def test_update_notes_replaces_the_notes() -> None:
    session = a_planned_session()
    session.update_notes(SessionNotes("Felt strong today."), clock=a_fixed_clock())
    assert session.notes == SessionNotes("Felt strong today.")


@pytest.mark.unit
def test_update_notes_accepts_an_explicitly_empty_value() -> None:
    """ "Notes may be empty" — round-tripping to empty is not an error."""
    session = a_planned_session()
    session.update_notes(SessionNotes("something"), clock=a_fixed_clock())
    session.update_notes(SessionNotes(""), clock=a_fixed_clock())
    assert session.notes == SessionNotes("")


@pytest.mark.unit
def test_update_notes_records_a_workout_session_notes_updated_event() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()
    notes = SessionNotes("Felt strong today.")

    session.update_notes(notes, clock=clock)

    events = session.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], WorkoutSessionNotesUpdated)
    assert events[0].session_id == session.id
    assert events[0].notes == notes
    assert events[0].occurred_at == clock.now()


@pytest.mark.unit
def test_update_notes_is_allowed_after_completion() -> None:
    """Deliberately not blocked, unlike Workout.update_notes/Exercise.
    update once terminal — the Bible's "corrections are appended as a
    note, never an overwrite" guidance for a Completed WorkoutSession
    means editing notes post-completion is the expected case."""
    session = a_planned_session()
    clock = a_fixed_clock()
    session.start(clock=clock)
    session.complete(
        duration=SessionDuration(timedelta(minutes=45)),
        completion_percentage=CompletionPercentage(100.0),
        clock=clock,
    )

    session.update_notes(SessionNotes("Correction: actually did 5 sets."), clock=clock)

    assert session.notes == SessionNotes("Correction: actually did 5 sets.")


@pytest.mark.unit
def test_update_notes_is_allowed_after_abandonment() -> None:
    session = a_planned_session()
    session.abandon(clock=a_fixed_clock())
    session.update_notes(SessionNotes("Had to stop early."), clock=a_fixed_clock())
    assert session.notes == SessionNotes("Had to stop early.")


# --- start() ---


@pytest.mark.unit
def test_start_moves_planned_to_active() -> None:
    session = a_planned_session()
    session.start(clock=a_fixed_clock())
    assert session.status == SessionStatus.ACTIVE


@pytest.mark.unit
def test_start_stamps_started_at_from_the_clock() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()
    session.start(clock=clock)
    assert session.started_at == clock.now()


@pytest.mark.unit
def test_start_records_a_workout_session_started_event() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()

    session.start(clock=clock)

    events = session.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], WorkoutSessionStarted)
    assert events[0].session_id == session.id
    assert events[0].workout_id == session.workout_id
    assert events[0].user_id == session.user_id
    assert events[0].occurred_at == clock.now()


@pytest.mark.unit
def test_cannot_start_twice() -> None:
    session = a_planned_session()
    session.start(clock=a_fixed_clock())
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        session.start(clock=a_fixed_clock())


@pytest.mark.unit
def test_cannot_start_an_abandoned_session() -> None:
    session = a_planned_session()
    session.abandon(clock=a_fixed_clock())
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        session.start(clock=a_fixed_clock())


@pytest.mark.unit
def test_cannot_start_a_completed_session() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()
    session.start(clock=clock)
    session.complete(
        duration=SessionDuration(timedelta(minutes=45)),
        completion_percentage=CompletionPercentage(100.0),
        clock=clock,
    )
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        session.start(clock=clock)


# --- complete() ---


@pytest.mark.unit
def test_complete_moves_active_to_completed() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()
    session.start(clock=clock)
    session.complete(
        duration=SessionDuration(timedelta(minutes=45)),
        completion_percentage=CompletionPercentage(100.0),
        clock=clock,
    )
    assert session.status == SessionStatus.COMPLETED


@pytest.mark.unit
def test_complete_stores_duration_completion_and_rating() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()
    session.start(clock=clock)
    duration = SessionDuration(timedelta(minutes=45))
    completion = CompletionPercentage(85.0)
    rating = SessionRating(8)

    session.complete(
        duration=duration, completion_percentage=completion, rating=rating, clock=clock
    )

    assert session.duration == duration
    assert session.completion_percentage == completion
    assert session.rating == rating
    assert session.completed_at == clock.now()


@pytest.mark.unit
def test_complete_without_a_rating_leaves_rating_none() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()
    session.start(clock=clock)
    session.complete(
        duration=SessionDuration(timedelta(minutes=45)),
        completion_percentage=CompletionPercentage(100.0),
        clock=clock,
    )
    assert session.rating is None


@pytest.mark.unit
def test_complete_records_a_workout_session_completed_event() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()
    session.start(clock=clock)
    session.pull_domain_events()  # drain WorkoutSessionStarted
    duration = SessionDuration(timedelta(minutes=45))
    completion = CompletionPercentage(100.0)

    session.complete(duration=duration, completion_percentage=completion, clock=clock)

    events = session.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], WorkoutSessionCompleted)
    assert events[0].session_id == session.id
    assert events[0].workout_id == session.workout_id
    assert events[0].user_id == session.user_id
    assert events[0].duration == duration
    assert events[0].completion_percentage == completion
    assert events[0].occurred_at == clock.now()


@pytest.mark.unit
def test_cannot_complete_before_starting() -> None:
    session = a_planned_session()
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        session.complete(
            duration=SessionDuration(timedelta(minutes=45)),
            completion_percentage=CompletionPercentage(100.0),
            clock=a_fixed_clock(),
        )


@pytest.mark.unit
def test_cannot_complete_twice() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()
    session.start(clock=clock)
    session.complete(
        duration=SessionDuration(timedelta(minutes=45)),
        completion_percentage=CompletionPercentage(100.0),
        clock=clock,
    )
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        session.complete(
            duration=SessionDuration(timedelta(minutes=30)),
            completion_percentage=CompletionPercentage(50.0),
            clock=clock,
        )


@pytest.mark.unit
def test_cannot_complete_an_abandoned_session() -> None:
    session = a_planned_session()
    session.abandon(clock=a_fixed_clock())
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        session.complete(
            duration=SessionDuration(timedelta(minutes=45)),
            completion_percentage=CompletionPercentage(100.0),
            clock=a_fixed_clock(),
        )


# --- abandon() ---


@pytest.mark.unit
def test_abandon_moves_planned_to_abandoned() -> None:
    session = a_planned_session()
    session.abandon(clock=a_fixed_clock())
    assert session.status == SessionStatus.ABANDONED


@pytest.mark.unit
def test_abandon_moves_active_to_abandoned() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()
    session.start(clock=clock)
    session.abandon(clock=clock)
    assert session.status == SessionStatus.ABANDONED


@pytest.mark.unit
def test_abandon_stamps_abandoned_at_from_the_clock() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()
    session.abandon(clock=clock)
    assert session.abandoned_at == clock.now()


@pytest.mark.unit
def test_abandon_without_duration_or_completion_leaves_them_none() -> None:
    session = a_planned_session()
    session.abandon(clock=a_fixed_clock())
    assert session.duration is None
    assert session.completion_percentage is None


@pytest.mark.unit
def test_abandon_can_record_a_partial_duration_and_completion() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()
    session.start(clock=clock)
    duration = SessionDuration(timedelta(minutes=15))
    completion = CompletionPercentage(30.0)

    session.abandon(duration=duration, completion_percentage=completion, clock=clock)

    assert session.duration == duration
    assert session.completion_percentage == completion


@pytest.mark.unit
def test_abandon_records_a_workout_session_abandoned_event() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()

    session.abandon(clock=clock)

    events = session.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], WorkoutSessionAbandoned)
    assert events[0].session_id == session.id
    assert events[0].workout_id == session.workout_id
    assert events[0].user_id == session.user_id
    assert events[0].occurred_at == clock.now()


@pytest.mark.unit
def test_cannot_abandon_after_completion() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()
    session.start(clock=clock)
    session.complete(
        duration=SessionDuration(timedelta(minutes=45)),
        completion_percentage=CompletionPercentage(100.0),
        clock=clock,
    )
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        session.abandon(clock=clock)


@pytest.mark.unit
def test_cannot_abandon_an_already_abandoned_session() -> None:
    session = a_planned_session()
    session.abandon(clock=a_fixed_clock())
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        session.abandon(clock=a_fixed_clock())


# --- full lifecycle ---


@pytest.mark.unit
def test_full_happy_path_lifecycle() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()

    session.start(clock=clock)
    session.complete(
        duration=SessionDuration(timedelta(minutes=45)),
        completion_percentage=CompletionPercentage(100.0),
        clock=clock,
    )

    assert session.status == SessionStatus.COMPLETED
    events = session.pull_domain_events()
    assert [type(event) for event in events] == [WorkoutSessionStarted, WorkoutSessionCompleted]


# --- __init__ construction (repository rehydration path) ---


@pytest.mark.unit
def test_constructor_rejects_a_naive_planned_at() -> None:
    with pytest.raises(DomainInvariantViolationError, match="timezone-aware"):
        WorkoutSession(
            WorkoutSessionId.generate(),
            workout_id=WorkoutId.generate(),
            user_id=UserId.generate(),
            session_date=SessionDate(date(2026, 1, 1)),
            planned_at=datetime(2026, 1, 1),  # deliberately naive
        )


@pytest.mark.unit
def test_constructor_rehydrates_an_existing_session_with_no_side_effects() -> None:
    """The path a repository uses to reconstruct a WorkoutSession already
    in storage — no event should be raised."""
    session = WorkoutSession(
        WorkoutSessionId.generate(),
        workout_id=WorkoutId.generate(),
        user_id=UserId.generate(),
        session_date=SessionDate(date(2026, 1, 1)),
        planned_at=datetime.now(timezone.utc),
        status=SessionStatus.ACTIVE,
        started_at=datetime.now(timezone.utc),
    )
    assert session.pull_domain_events() == []
    assert session.status == SessionStatus.ACTIVE


@pytest.mark.unit
def test_constructor_accepts_explicit_optional_fields() -> None:
    duration = SessionDuration(timedelta(minutes=45))
    completion = CompletionPercentage(100.0)
    rating = SessionRating(9)
    now = datetime.now(timezone.utc)
    session = WorkoutSession(
        WorkoutSessionId.generate(),
        workout_id=WorkoutId.generate(),
        user_id=UserId.generate(),
        session_date=SessionDate(date(2026, 1, 1)),
        planned_at=now,
        status=SessionStatus.COMPLETED,
        notes=SessionNotes("Great session."),
        duration=duration,
        completion_percentage=completion,
        rating=rating,
        started_at=now,
        completed_at=now,
    )
    assert session.notes == SessionNotes("Great session.")
    assert session.duration == duration
    assert session.completion_percentage == completion
    assert session.rating == rating
    assert session.started_at == now
    assert session.completed_at == now
    assert session.abandoned_at is None
