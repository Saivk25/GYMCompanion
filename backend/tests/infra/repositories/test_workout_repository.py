"""Integration tests for `WorkoutSqlRepository` against a real, migrated
Postgres database. See `test_user_repository.py`'s module docstring for the
shared fixture convention.

`workouts.user_id` is a foreign key to `users.user_id`, so every test here
first creates and commits a `User` row before creating a `Workout` for it —
the same dependency order the domain itself requires (a `Workout` always
belongs to an already-registered `User`).
"""

from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.domain.shared_kernel.clock import FixedClock
from app.domain.user.identifiers import UserId
from app.domain.user.user import User
from app.domain.user.value_objects import AuthMethod, Locale, Timezone
from app.domain.workout.enums import WorkoutStatus
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.value_objects import WorkoutDate, WorkoutDuration, WorkoutName
from app.domain.workout.workout import Workout
from app.infra.database import tenant_scope
from app.infra.repositories.user_repository import UserSqlRepository
from app.infra.repositories.workout_repository import WorkoutSqlRepository

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


@pytest.mark.integration
def test_add_and_get_round_trip(session_factory: sessionmaker[Session]) -> None:
    user_id = _create_user(session_factory)
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

    with session_factory() as session, tenant_scope(session, str(user_id)):
        fetched = WorkoutSqlRepository(session).get(workout_id)

    assert fetched is not None
    assert fetched.user_id == user_id
    assert fetched.name == WorkoutName("Push Day")
    assert fetched.status is WorkoutStatus.PLANNED


@pytest.mark.integration
def test_mutation_persists_without_a_second_add_call(
    session_factory: sessionmaker[Session],
) -> None:
    user_id = _create_user(session_factory)
    workout_id = WorkoutId.generate()
    workout = Workout.plan(
        workout_id=workout_id,
        user_id=user_id,
        name=WorkoutName("Leg Day"),
        planned_date=WorkoutDate(date(2026, 1, 3)),
        clock=_CLOCK,
    )

    with session_factory() as session:
        WorkoutSqlRepository(session).add(workout)
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        repository = WorkoutSqlRepository(session)
        fetched = repository.get(workout_id)
        assert fetched is not None
        fetched.start(clock=_CLOCK)
        fetched.complete(duration=WorkoutDuration(timedelta(hours=1)), clock=_CLOCK)
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        refetched = WorkoutSqlRepository(session).get(workout_id)

    assert refetched is not None
    assert refetched.status is WorkoutStatus.COMPLETED
    assert refetched.duration == WorkoutDuration(timedelta(hours=1))


@pytest.mark.integration
def test_list_by_user_returns_only_that_users_workouts(
    session_factory: sessionmaker[Session],
) -> None:
    user_a = _create_user(session_factory)
    user_b = _create_user(session_factory)

    for user_id, name in ((user_a, "A1"), (user_a, "A2"), (user_b, "B1")):
        workout = Workout.plan(
            workout_id=WorkoutId.generate(),
            user_id=user_id,
            name=WorkoutName(name),
            planned_date=WorkoutDate(date(2026, 1, 4)),
            clock=_CLOCK,
        )
        with session_factory() as session:
            WorkoutSqlRepository(session).add(workout)
            session.commit()

    with session_factory() as session:
        workouts_for_a = WorkoutSqlRepository(session).list_by_user(user_a)

    assert {w.name.value for w in workouts_for_a} == {"A1", "A2"}


@pytest.mark.integration
def test_remove_deletes_the_row(session_factory: sessionmaker[Session]) -> None:
    user_id = _create_user(session_factory)
    workout_id = WorkoutId.generate()
    workout = Workout.plan(
        workout_id=workout_id,
        user_id=user_id,
        name=WorkoutName("Rest Day"),
        planned_date=WorkoutDate(date(2026, 1, 5)),
        clock=_CLOCK,
    )

    with session_factory() as session:
        repository = WorkoutSqlRepository(session)
        repository.add(workout)
        session.commit()
        repository.remove(workout)
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        assert WorkoutSqlRepository(session).get(workout_id) is None
