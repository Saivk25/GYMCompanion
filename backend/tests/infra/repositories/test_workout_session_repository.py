"""Integration tests for `WorkoutSessionSqlRepository` against a real,
migrated Postgres database. See `test_user_repository.py`'s module
docstring for the shared fixture convention.

Every test here first creates a `User`, `Workout`, and `Exercise` row —
`workout_sessions`/`exercise_performances` both carry foreign keys to
rows these tests must create first, the same dependency order the domain
itself requires.
"""

from datetime import date, datetime, timezone

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.domain.exercise.enums import Difficulty, MovementPattern
from app.domain.exercise.exercise import Exercise
from app.domain.exercise.identifiers import ExerciseId
from app.domain.exercise.value_objects import ExerciseInstructions, ExerciseName
from app.domain.shared_kernel.clock import FixedClock
from app.domain.user.identifiers import UserId
from app.domain.user.user import User
from app.domain.user.value_objects import AuthMethod, Locale, Timezone
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.value_objects import WorkoutDate, WorkoutName
from app.domain.workout.workout import Workout
from app.domain.workout_session.enums import SessionStatus
from app.domain.workout_session.exercise_set import (
    ExerciseSet,
    SetNumber,
    SetReps,
    SetRPE,
    SetWeight,
)
from app.domain.workout_session.identifiers import WorkoutSessionId
from app.domain.workout_session.value_objects import SessionDate
from app.domain.workout_session.workout_session import WorkoutSession
from app.infra.database import tenant_scope
from app.infra.repositories.exercise_repository import ExerciseSqlRepository
from app.infra.repositories.user_repository import UserSqlRepository
from app.infra.repositories.workout_repository import WorkoutSqlRepository
from app.infra.repositories.workout_session_repository import WorkoutSessionSqlRepository

_CLOCK = FixedClock(datetime(2026, 1, 1, tzinfo=timezone.utc))


def _create_user(session_factory: sessionmaker[Session]) -> UserId:
    user_id = UserId.generate()
    user = User.register(
        user_id=user_id,
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        auth_method=AuthMethod("password"),
        clock=_CLOCK,
    )
    with session_factory() as session:
        UserSqlRepository(session).add(user)
        session.commit()
    return user_id


def _create_workout(session_factory: sessionmaker[Session], user_id: UserId) -> WorkoutId:
    workout_id = WorkoutId.generate()
    workout = Workout.plan(
        workout_id=workout_id,
        user_id=user_id,
        name=WorkoutName("Push Day"),
        planned_date=WorkoutDate(date(2026, 1, 2)),
        clock=_CLOCK,
    )
    with session_factory() as session:
        WorkoutSqlRepository(session).add(workout)
        session.commit()
    return workout_id


def _create_exercise(session_factory: sessionmaker[Session]) -> ExerciseId:
    exercise_id = ExerciseId.generate()
    exercise = Exercise.create(
        exercise_id=exercise_id,
        name=ExerciseName("Barbell Bench Press"),
        movement_pattern=MovementPattern.PUSH,
        difficulty=Difficulty.INTERMEDIATE,
        instructions=ExerciseInstructions("Lie on a bench, lower the bar, press up."),
        clock=_CLOCK,
    )
    with session_factory() as session:
        ExerciseSqlRepository(session).add(exercise)
        session.commit()
    return exercise_id


@pytest.mark.integration
def test_add_and_get_round_trip(session_factory: sessionmaker[Session]) -> None:
    user_id = _create_user(session_factory)
    workout_id = _create_workout(session_factory, user_id)
    session_id = WorkoutSessionId.generate()
    workout_session = WorkoutSession.plan(
        session_id=session_id,
        workout_id=workout_id,
        user_id=user_id,
        session_date=SessionDate(date(2026, 1, 2)),
        clock=_CLOCK,
    )

    with session_factory() as session:
        WorkoutSessionSqlRepository(session).add(workout_session)
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        fetched = WorkoutSessionSqlRepository(session).get(session_id)

    assert fetched is not None
    assert fetched.workout_id == workout_id
    assert fetched.status is SessionStatus.PLANNED
    assert fetched.exercise_performances == ()


@pytest.mark.integration
def test_add_exercise_and_log_set_persist_without_a_second_add_call(
    session_factory: sessionmaker[Session],
) -> None:
    """Exercises `WorkoutSessionSqlRepository`'s multi-table reconciliation
    (see its module docstring): a session fetched via `get()`, then mutated
    with `add_exercise()`/`log_set()`, must persist both the new child rows
    on `session.commit()` with no second `add()` call — the same
    tracking-and-sync mechanism `_tracking.py` provides for every other
    repository, applied here across three tables instead of one.
    """
    user_id = _create_user(session_factory)
    workout_id = _create_workout(session_factory, user_id)
    exercise_id = _create_exercise(session_factory)
    session_id = WorkoutSessionId.generate()
    workout_session = WorkoutSession.plan(
        session_id=session_id,
        workout_id=workout_id,
        user_id=user_id,
        session_date=SessionDate(date(2026, 1, 2)),
        clock=_CLOCK,
    )

    with session_factory() as session:
        WorkoutSessionSqlRepository(session).add(workout_session)
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        repository = WorkoutSessionSqlRepository(session)
        fetched = repository.get(session_id)
        assert fetched is not None
        performance_id = fetched.add_exercise(exercise_id, clock=_CLOCK)
        fetched.log_set(
            performance_id,
            ExerciseSet(
                set_number=SetNumber(1),
                weight=SetWeight(60.0),
                reps=SetReps(8),
                rpe=SetRPE(7),
            ),
            clock=_CLOCK,
        )
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        refetched = WorkoutSessionSqlRepository(session).get(session_id)

    assert refetched is not None
    assert len(refetched.exercise_performances) == 1
    performance = refetched.exercise_performances[0]
    assert performance.exercise_id == exercise_id
    assert len(performance.sets) == 1
    assert performance.sets[0].weight == SetWeight(60.0)
    assert performance.sets[0].reps == SetReps(8)


@pytest.mark.integration
def test_remove_exercise_deletes_its_sets_too(session_factory: sessionmaker[Session]) -> None:
    user_id = _create_user(session_factory)
    workout_id = _create_workout(session_factory, user_id)
    exercise_id = _create_exercise(session_factory)
    session_id = WorkoutSessionId.generate()
    workout_session = WorkoutSession.plan(
        session_id=session_id,
        workout_id=workout_id,
        user_id=user_id,
        session_date=SessionDate(date(2026, 1, 2)),
        clock=_CLOCK,
    )

    with session_factory() as session:
        WorkoutSessionSqlRepository(session).add(workout_session)
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        repository = WorkoutSessionSqlRepository(session)
        fetched = repository.get(session_id)
        assert fetched is not None
        performance_id = fetched.add_exercise(exercise_id, clock=_CLOCK)
        fetched.log_set(
            performance_id,
            ExerciseSet(
                set_number=SetNumber(1), weight=SetWeight(60.0), reps=SetReps(8), rpe=SetRPE(7)
            ),
            clock=_CLOCK,
        )
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        repository = WorkoutSessionSqlRepository(session)
        fetched = repository.get(session_id)
        assert fetched is not None
        fetched.remove_exercise(performance_id, clock=_CLOCK)
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        refetched = WorkoutSessionSqlRepository(session).get(session_id)

    assert refetched is not None
    assert refetched.exercise_performances == ()


@pytest.mark.integration
def test_remove_deletes_session_and_children(session_factory: sessionmaker[Session]) -> None:
    user_id = _create_user(session_factory)
    workout_id = _create_workout(session_factory, user_id)
    session_id = WorkoutSessionId.generate()
    workout_session = WorkoutSession.plan(
        session_id=session_id,
        workout_id=workout_id,
        user_id=user_id,
        session_date=SessionDate(date(2026, 1, 2)),
        clock=_CLOCK,
    )

    with session_factory() as session:
        repository = WorkoutSessionSqlRepository(session)
        repository.add(workout_session)
        session.commit()
        repository.remove(workout_session)
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        assert WorkoutSessionSqlRepository(session).get(session_id) is None
