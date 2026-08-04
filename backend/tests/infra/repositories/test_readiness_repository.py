"""Integration tests for `ReadinessSqlRepository` against a real, migrated
Postgres database. See `test_progress_repository.py`'s module docstring for
the shared fixture/foreign-key convention these tests follow.
"""

from datetime import date, datetime, timezone

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.domain.readiness.enums import ReadinessSource
from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.readiness import Readiness
from app.domain.readiness.value_objects import EnergyLevel, ReadinessDate, SleepQuality
from app.domain.shared_kernel.clock import FixedClock
from app.domain.user.identifiers import UserId
from app.domain.user.user import User
from app.domain.user.value_objects import AuthMethod, Locale, Timezone
from app.infra.database import tenant_scope
from app.infra.repositories.readiness_repository import ReadinessSqlRepository
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
    readiness_id = ReadinessId.generate()
    readiness = Readiness.record(
        readiness_id=readiness_id,
        user_id=user_id,
        readiness_date=ReadinessDate(date(2026, 1, 2)),
        clock=_CLOCK,
        source=ReadinessSource.MANUAL,
        energy_level=EnergyLevel(7),
        sleep_quality=SleepQuality(8),
    )

    with session_factory() as session:
        ReadinessSqlRepository(session).add(readiness)
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        fetched = ReadinessSqlRepository(session).get(readiness_id)

    assert fetched is not None
    assert fetched.source is ReadinessSource.MANUAL
    assert fetched.energy_level == EnergyLevel(7)
    assert fetched.sleep_quality == SleepQuality(8)


@pytest.mark.integration
def test_mutation_persists_without_a_second_add_call(
    session_factory: sessionmaker[Session],
) -> None:
    user_id = _create_user(session_factory)
    readiness_id = ReadinessId.generate()
    readiness = Readiness.record(
        readiness_id=readiness_id,
        user_id=user_id,
        readiness_date=ReadinessDate(date(2026, 1, 2)),
        clock=_CLOCK,
    )

    with session_factory() as session:
        ReadinessSqlRepository(session).add(readiness)
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        repository = ReadinessSqlRepository(session)
        fetched = repository.get(readiness_id)
        assert fetched is not None
        fetched.update_recovery_metrics(clock=_CLOCK, energy_level=EnergyLevel(9))
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        refetched = ReadinessSqlRepository(session).get(readiness_id)

    assert refetched is not None
    assert refetched.energy_level == EnergyLevel(9)


@pytest.mark.integration
def test_list_by_user_returns_only_that_users_checkins(
    session_factory: sessionmaker[Session],
) -> None:
    user_a = _create_user(session_factory)
    user_b = _create_user(session_factory)

    for user_id in (user_a, user_a, user_b):
        readiness = Readiness.record(
            readiness_id=ReadinessId.generate(),
            user_id=user_id,
            readiness_date=ReadinessDate(date(2026, 1, 2)),
            clock=_CLOCK,
        )
        with session_factory() as session:
            ReadinessSqlRepository(session).add(readiness)
            session.commit()

    with session_factory() as session:
        checkins_for_a = ReadinessSqlRepository(session).list_by_user(user_a)

    assert len(checkins_for_a) == 2
    assert all(checkin.user_id == user_a for checkin in checkins_for_a)


@pytest.mark.integration
def test_remove_deletes_the_row(session_factory: sessionmaker[Session]) -> None:
    user_id = _create_user(session_factory)
    readiness_id = ReadinessId.generate()
    readiness = Readiness.record(
        readiness_id=readiness_id,
        user_id=user_id,
        readiness_date=ReadinessDate(date(2026, 1, 2)),
        clock=_CLOCK,
    )

    with session_factory() as session:
        repository = ReadinessSqlRepository(session)
        repository.add(readiness)
        session.commit()
        repository.remove(readiness)
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        assert ReadinessSqlRepository(session).get(readiness_id) is None
