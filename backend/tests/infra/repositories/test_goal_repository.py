"""Integration tests for `GoalSqlRepository` against a real, migrated
Postgres database. See `test_progress_repository.py`'s module docstring for
the shared fixture/foreign-key convention these tests follow.
"""

from datetime import date, datetime, timezone

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.domain.goal.enums import GoalStatus, GoalType
from app.domain.goal.goal import Goal
from app.domain.goal.identifiers import GoalId
from app.domain.goal.value_objects import GoalName, TargetDate, TargetWeight
from app.domain.shared_kernel.clock import FixedClock
from app.domain.user.identifiers import UserId
from app.domain.user.user import User
from app.domain.user.value_objects import AuthMethod, Locale, Timezone
from app.infra.database import tenant_scope
from app.infra.repositories.goal_repository import GoalSqlRepository
from app.infra.repositories.user_repository import UserSqlRepository

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
    goal_id = GoalId.generate()
    goal = Goal.create(
        goal_id=goal_id,
        user_id=user_id,
        goal_type=GoalType.LOSE_FAT,
        name=GoalName("Lose 5kg by June"),
        target_date=TargetDate(date(2026, 6, 1)),
        clock=_CLOCK,
        target_weight=TargetWeight(75.0),
    )

    with session_factory() as session:
        GoalSqlRepository(session).add(goal)
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        fetched = GoalSqlRepository(session).get(goal_id)

    assert fetched is not None
    assert fetched.goal_type is GoalType.LOSE_FAT
    assert fetched.name == GoalName("Lose 5kg by June")
    assert fetched.target_weight == TargetWeight(75.0)
    assert fetched.status is GoalStatus.ACTIVE


@pytest.mark.integration
def test_mutation_persists_without_a_second_add_call(
    session_factory: sessionmaker[Session],
) -> None:
    user_id = _create_user(session_factory)
    goal_id = GoalId.generate()
    goal = Goal.create(
        goal_id=goal_id,
        user_id=user_id,
        goal_type=GoalType.STRENGTH,
        name=GoalName("Squat 100kg"),
        target_date=TargetDate(date(2026, 12, 1)),
        clock=_CLOCK,
    )

    with session_factory() as session:
        GoalSqlRepository(session).add(goal)
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        repository = GoalSqlRepository(session)
        fetched = repository.get(goal_id)
        assert fetched is not None
        fetched.complete(clock=_CLOCK)
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        refetched = GoalSqlRepository(session).get(goal_id)

    assert refetched is not None
    assert refetched.status is GoalStatus.COMPLETED


@pytest.mark.integration
def test_list_by_user_returns_only_that_users_goals(session_factory: sessionmaker[Session]) -> None:
    user_a = _create_user(session_factory)
    user_b = _create_user(session_factory)

    for user_id in (user_a, user_a, user_b):
        goal = Goal.create(
            goal_id=GoalId.generate(),
            user_id=user_id,
            goal_type=GoalType.MAINTAIN,
            name=GoalName("Stay consistent"),
            target_date=TargetDate(date(2026, 12, 1)),
            clock=_CLOCK,
        )
        with session_factory() as session:
            GoalSqlRepository(session).add(goal)
            session.commit()

    with session_factory() as session:
        goals_for_a = GoalSqlRepository(session).list_by_user(user_a)

    assert len(goals_for_a) == 2
    assert all(goal.user_id == user_a for goal in goals_for_a)


@pytest.mark.integration
def test_remove_deletes_the_row(session_factory: sessionmaker[Session]) -> None:
    user_id = _create_user(session_factory)
    goal_id = GoalId.generate()
    goal = Goal.create(
        goal_id=goal_id,
        user_id=user_id,
        goal_type=GoalType.ENDURANCE,
        name=GoalName("Run a 10k"),
        target_date=TargetDate(date(2026, 9, 1)),
        clock=_CLOCK,
    )

    with session_factory() as session:
        repository = GoalSqlRepository(session)
        repository.add(goal)
        session.commit()
        repository.remove(goal)
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        assert GoalSqlRepository(session).get(goal_id) is None
