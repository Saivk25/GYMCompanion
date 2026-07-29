"""Tests for app/domain/workout_session/workout_session.py."""

from datetime import date, datetime, timedelta, timezone

import pytest

from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout_session.enums import SessionStatus
from app.domain.workout_session.events import (
    ExerciseAddedToSession,
    ExercisePerformanceUpdated,
    ExerciseRemovedFromSession,
    ExerciseSetCompleted,
    WorkoutSessionAbandoned,
    WorkoutSessionCompleted,
    WorkoutSessionNotesUpdated,
    WorkoutSessionStarted,
)
from app.domain.workout_session.exercise_performance import ExercisePerformance, PerformanceNotes
from app.domain.workout_session.identifiers import ExercisePerformanceId, WorkoutSessionId
from app.domain.workout_session.value_objects import (
    CompletionPercentage,
    SessionDate,
    SessionDuration,
    SessionNotes,
    SessionRating,
)
from app.domain.workout_session.workout_session import WorkoutSession
from tests.domain.workout_session.factories import (
    a_fixed_clock,
    a_planned_session,
    an_active_session,
    an_exercise_id,
    an_exercise_set,
)

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


@pytest.mark.unit
def test_constructor_accepts_explicit_exercise_performances() -> None:
    performance = ExercisePerformance(
        ExercisePerformanceId.generate(), exercise_id=an_exercise_id()
    )
    session = WorkoutSession(
        WorkoutSessionId.generate(),
        workout_id=WorkoutId.generate(),
        user_id=UserId.generate(),
        session_date=SessionDate(date(2026, 1, 1)),
        planned_at=datetime.now(timezone.utc),
        exercise_performances=(performance,),
    )
    assert session.exercise_performances == (performance,)


# --- add_exercise() ---


@pytest.mark.unit
def test_add_exercise_creates_a_new_performance_and_returns_its_id() -> None:
    session = a_planned_session()
    exercise_id = an_exercise_id()

    performance_id = session.add_exercise(exercise_id, clock=a_fixed_clock())

    assert len(session.exercise_performances) == 1
    performance = session.exercise_performances[0]
    assert performance.id == performance_id
    assert performance.exercise_id == exercise_id
    assert performance.sets == ()


@pytest.mark.unit
def test_add_exercise_accepts_optional_notes() -> None:
    session = a_planned_session()
    notes = PerformanceNotes("Warm-up sets excluded.")

    session.add_exercise(an_exercise_id(), clock=a_fixed_clock(), notes=notes)

    assert session.exercise_performances[0].notes == notes


@pytest.mark.unit
def test_add_exercise_records_an_exercise_added_to_session_event() -> None:
    session = a_planned_session()
    exercise_id = an_exercise_id()
    clock = a_fixed_clock()

    performance_id = session.add_exercise(exercise_id, clock=clock)

    events = session.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], ExerciseAddedToSession)
    assert events[0].session_id == session.id
    assert events[0].performance_id == performance_id
    assert events[0].exercise_id == exercise_id
    assert events[0].occurred_at == clock.now()


@pytest.mark.unit
def test_add_exercise_is_allowed_while_active() -> None:
    session = an_active_session()
    session.add_exercise(an_exercise_id(), clock=a_fixed_clock())
    assert len(session.exercise_performances) == 1


@pytest.mark.unit
def test_cannot_add_exercise_once_completed() -> None:
    session = an_active_session()
    session.complete(
        duration=SessionDuration(timedelta(minutes=45)),
        completion_percentage=CompletionPercentage(100.0),
        clock=a_fixed_clock(),
    )
    with pytest.raises(DomainInvariantViolationError, match="cannot modify"):
        session.add_exercise(an_exercise_id(), clock=a_fixed_clock())


@pytest.mark.unit
def test_cannot_add_exercise_once_abandoned() -> None:
    session = a_planned_session()
    session.abandon(clock=a_fixed_clock())
    with pytest.raises(DomainInvariantViolationError, match="cannot modify"):
        session.add_exercise(an_exercise_id(), clock=a_fixed_clock())


# --- remove_exercise() ---


@pytest.mark.unit
def test_remove_exercise_removes_the_performance() -> None:
    session = a_planned_session()
    performance_id = session.add_exercise(an_exercise_id(), clock=a_fixed_clock())

    session.remove_exercise(performance_id, clock=a_fixed_clock())

    assert session.exercise_performances == ()


@pytest.mark.unit
def test_remove_exercise_leaves_other_performances_untouched() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()
    kept_id = session.add_exercise(an_exercise_id(), clock=clock)
    removed_id = session.add_exercise(an_exercise_id(), clock=clock)

    session.remove_exercise(removed_id, clock=clock)

    assert [p.id for p in session.exercise_performances] == [kept_id]


@pytest.mark.unit
def test_remove_exercise_records_an_exercise_removed_from_session_event() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()
    exercise_id = an_exercise_id()
    performance_id = session.add_exercise(exercise_id, clock=clock)
    session.pull_domain_events()  # drain ExerciseAddedToSession

    session.remove_exercise(performance_id, clock=clock)

    events = session.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], ExerciseRemovedFromSession)
    assert events[0].session_id == session.id
    assert events[0].performance_id == performance_id
    assert events[0].exercise_id == exercise_id


@pytest.mark.unit
def test_remove_exercise_raises_for_an_unknown_performance_id() -> None:
    session = a_planned_session()
    with pytest.raises(DomainInvariantViolationError, match="no exercise performance"):
        session.remove_exercise(ExercisePerformanceId.generate(), clock=a_fixed_clock())


@pytest.mark.unit
def test_cannot_remove_exercise_once_completed() -> None:
    session = an_active_session()
    performance_id = session.add_exercise(an_exercise_id(), clock=a_fixed_clock())
    session.complete(
        duration=SessionDuration(timedelta(minutes=45)),
        completion_percentage=CompletionPercentage(100.0),
        clock=a_fixed_clock(),
    )
    with pytest.raises(DomainInvariantViolationError, match="cannot modify"):
        session.remove_exercise(performance_id, clock=a_fixed_clock())


@pytest.mark.unit
def test_cannot_remove_exercise_once_abandoned() -> None:
    session = a_planned_session()
    performance_id = session.add_exercise(an_exercise_id(), clock=a_fixed_clock())
    session.abandon(clock=a_fixed_clock())
    with pytest.raises(DomainInvariantViolationError, match="cannot modify"):
        session.remove_exercise(performance_id, clock=a_fixed_clock())


# --- log_set() ---


@pytest.mark.unit
def test_log_set_appends_a_set_to_the_named_performance() -> None:
    session = a_planned_session()
    performance_id = session.add_exercise(an_exercise_id(), clock=a_fixed_clock())
    exercise_set = an_exercise_set(set_number=1)

    session.log_set(performance_id, exercise_set, clock=a_fixed_clock())

    assert session.exercise_performances[0].sets == (exercise_set,)


@pytest.mark.unit
def test_log_set_rejects_a_duplicate_set_number() -> None:
    session = a_planned_session()
    performance_id = session.add_exercise(an_exercise_id(), clock=a_fixed_clock())
    session.log_set(performance_id, an_exercise_set(set_number=1), clock=a_fixed_clock())

    with pytest.raises(DomainInvariantViolationError, match="duplicate set number"):
        session.log_set(performance_id, an_exercise_set(set_number=1), clock=a_fixed_clock())


@pytest.mark.unit
def test_log_set_records_an_exercise_performance_updated_event() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()
    exercise_id = an_exercise_id()
    performance_id = session.add_exercise(exercise_id, clock=clock)
    session.pull_domain_events()  # drain ExerciseAddedToSession

    session.log_set(performance_id, an_exercise_set(set_number=1), clock=clock)

    events = session.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], ExercisePerformanceUpdated)
    assert events[0].session_id == session.id
    assert events[0].performance_id == performance_id
    assert events[0].exercise_id == exercise_id


@pytest.mark.unit
def test_log_set_raises_for_an_unknown_performance_id() -> None:
    session = a_planned_session()
    with pytest.raises(DomainInvariantViolationError, match="no exercise performance"):
        session.log_set(ExercisePerformanceId.generate(), an_exercise_set(), clock=a_fixed_clock())


@pytest.mark.unit
def test_cannot_log_set_once_completed() -> None:
    session = an_active_session()
    performance_id = session.add_exercise(an_exercise_id(), clock=a_fixed_clock())
    session.complete(
        duration=SessionDuration(timedelta(minutes=45)),
        completion_percentage=CompletionPercentage(100.0),
        clock=a_fixed_clock(),
    )
    with pytest.raises(DomainInvariantViolationError, match="cannot modify"):
        session.log_set(performance_id, an_exercise_set(), clock=a_fixed_clock())


@pytest.mark.unit
def test_cannot_log_set_once_abandoned() -> None:
    session = a_planned_session()
    performance_id = session.add_exercise(an_exercise_id(), clock=a_fixed_clock())
    session.abandon(clock=a_fixed_clock())
    with pytest.raises(DomainInvariantViolationError, match="cannot modify"):
        session.log_set(performance_id, an_exercise_set(), clock=a_fixed_clock())


# --- complete_set() ---


@pytest.mark.unit
def test_complete_set_marks_the_set_complete() -> None:
    session = a_planned_session()
    performance_id = session.add_exercise(an_exercise_id(), clock=a_fixed_clock())
    session.log_set(performance_id, an_exercise_set(set_number=1), clock=a_fixed_clock())

    session.complete_set(performance_id, 1, clock=a_fixed_clock())

    assert session.exercise_performances[0].sets[0].completed is True


@pytest.mark.unit
def test_complete_set_records_an_exercise_set_completed_event() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()
    exercise_id = an_exercise_id()
    performance_id = session.add_exercise(exercise_id, clock=clock)
    session.log_set(performance_id, an_exercise_set(set_number=1), clock=clock)
    session.pull_domain_events()  # drain ExerciseAddedToSession, ExercisePerformanceUpdated

    session.complete_set(performance_id, 1, clock=clock)

    events = session.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], ExerciseSetCompleted)
    assert events[0].session_id == session.id
    assert events[0].performance_id == performance_id
    assert events[0].exercise_id == exercise_id
    assert events[0].exercise_set.completed is True
    assert events[0].exercise_set.set_number.value == 1


@pytest.mark.unit
def test_complete_set_raises_for_an_unknown_performance_id() -> None:
    session = a_planned_session()
    with pytest.raises(DomainInvariantViolationError, match="no exercise performance"):
        session.complete_set(ExercisePerformanceId.generate(), 1, clock=a_fixed_clock())


@pytest.mark.unit
def test_complete_set_raises_for_an_unknown_set_number() -> None:
    session = a_planned_session()
    performance_id = session.add_exercise(an_exercise_id(), clock=a_fixed_clock())
    with pytest.raises(DomainInvariantViolationError, match="no set numbered"):
        session.complete_set(performance_id, 1, clock=a_fixed_clock())


@pytest.mark.unit
def test_cannot_complete_set_once_completed() -> None:
    session = an_active_session()
    performance_id = session.add_exercise(an_exercise_id(), clock=a_fixed_clock())
    session.log_set(performance_id, an_exercise_set(set_number=1), clock=a_fixed_clock())
    session.complete(
        duration=SessionDuration(timedelta(minutes=45)),
        completion_percentage=CompletionPercentage(100.0),
        clock=a_fixed_clock(),
    )
    with pytest.raises(DomainInvariantViolationError, match="cannot modify"):
        session.complete_set(performance_id, 1, clock=a_fixed_clock())


@pytest.mark.unit
def test_cannot_complete_set_once_abandoned() -> None:
    session = a_planned_session()
    performance_id = session.add_exercise(an_exercise_id(), clock=a_fixed_clock())
    session.log_set(performance_id, an_exercise_set(set_number=1), clock=a_fixed_clock())
    session.abandon(clock=a_fixed_clock())
    with pytest.raises(DomainInvariantViolationError, match="cannot modify"):
        session.complete_set(performance_id, 1, clock=a_fixed_clock())


# --- update_exercise_notes() ---


@pytest.mark.unit
def test_update_exercise_notes_replaces_the_performance_notes() -> None:
    session = a_planned_session()
    performance_id = session.add_exercise(an_exercise_id(), clock=a_fixed_clock())
    notes = PerformanceNotes("Switched to dumbbells.")

    session.update_exercise_notes(performance_id, notes, clock=a_fixed_clock())

    assert session.exercise_performances[0].notes == notes


@pytest.mark.unit
def test_update_exercise_notes_records_an_exercise_performance_updated_event() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()
    exercise_id = an_exercise_id()
    performance_id = session.add_exercise(exercise_id, clock=clock)
    session.pull_domain_events()  # drain ExerciseAddedToSession

    session.update_exercise_notes(performance_id, PerformanceNotes("Note."), clock=clock)

    events = session.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], ExercisePerformanceUpdated)
    assert events[0].session_id == session.id
    assert events[0].performance_id == performance_id
    assert events[0].exercise_id == exercise_id


@pytest.mark.unit
def test_update_exercise_notes_raises_for_an_unknown_performance_id() -> None:
    session = a_planned_session()
    with pytest.raises(DomainInvariantViolationError, match="no exercise performance"):
        session.update_exercise_notes(
            ExercisePerformanceId.generate(), PerformanceNotes("x"), clock=a_fixed_clock()
        )


@pytest.mark.unit
def test_cannot_update_exercise_notes_once_completed() -> None:
    """Deliberately different from `WorkoutSession.update_notes()`, which
    stays open post-completion — see that method's docstring on
    `workout_session.py` for why session-level notes and per-exercise
    performance data are treated differently."""
    session = an_active_session()
    performance_id = session.add_exercise(an_exercise_id(), clock=a_fixed_clock())
    session.complete(
        duration=SessionDuration(timedelta(minutes=45)),
        completion_percentage=CompletionPercentage(100.0),
        clock=a_fixed_clock(),
    )
    with pytest.raises(DomainInvariantViolationError, match="cannot modify"):
        session.update_exercise_notes(performance_id, PerformanceNotes("x"), clock=a_fixed_clock())


@pytest.mark.unit
def test_cannot_update_exercise_notes_once_abandoned() -> None:
    session = a_planned_session()
    performance_id = session.add_exercise(an_exercise_id(), clock=a_fixed_clock())
    session.abandon(clock=a_fixed_clock())
    with pytest.raises(DomainInvariantViolationError, match="cannot modify"):
        session.update_exercise_notes(performance_id, PerformanceNotes("x"), clock=a_fixed_clock())


# --- full lifecycle with exercise performances ---


@pytest.mark.unit
def test_full_lifecycle_with_exercises_and_sets() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()

    session.start(clock=clock)
    performance_id = session.add_exercise(an_exercise_id(), clock=clock)
    session.log_set(performance_id, an_exercise_set(set_number=1), clock=clock)
    session.log_set(performance_id, an_exercise_set(set_number=2), clock=clock)
    session.complete_set(performance_id, 1, clock=clock)
    session.complete(
        duration=SessionDuration(timedelta(minutes=45)),
        completion_percentage=CompletionPercentage(100.0),
        clock=clock,
    )

    performance = session.exercise_performances[0]
    assert len(performance.sets) == 2
    assert performance.sets[0].completed is True
    assert performance.sets[1].completed is False
    assert session.status == SessionStatus.COMPLETED
