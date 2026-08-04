"""Integration tests for `ProgressSqlRepository` against a real, migrated
Postgres database. See `test_user_repository.py`'s module docstring for the
shared fixture convention, and `test_workout_repository.py`'s for why a
`User` row is created first (`progress_records.user_id` is a foreign key).
"""

from datetime import date, datetime, timezone

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.domain.progress.enums import MeasurementUnit, ProgressSource
from app.domain.progress.identifiers import ProgressId
from app.domain.progress.progress import Progress
from app.domain.progress.value_objects import BodyWeight, ProgressDate
from app.domain.shared_kernel.clock import FixedClock
from app.domain.user.identifiers import UserId
from app.domain.user.user import User
from app.domain.user.value_objects import AuthMethod, Locale, Timezone
from app.infra.database import tenant_scope
from app.infra.repositories.progress_repository import ProgressSqlRepository
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
    progress_id = ProgressId.generate()
    progress = Progress.record(
        progress_id=progress_id,
        user_id=user_id,
        progress_date=ProgressDate(date(2026, 1, 2)),
        unit=MeasurementUnit.METRIC,
        source=ProgressSource.MANUAL,
        clock=_CLOCK,
        body_weight=BodyWeight(82.5),
    )

    with session_factory() as session:
        ProgressSqlRepository(session).add(progress)
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        fetched = ProgressSqlRepository(session).get(progress_id)

    assert fetched is not None
    assert fetched.body_weight == BodyWeight(82.5)
    assert fetched.unit is MeasurementUnit.METRIC


@pytest.mark.integration
def test_mutation_persists_without_a_second_add_call(
    session_factory: sessionmaker[Session],
) -> None:
    user_id = _create_user(session_factory)
    progress_id = ProgressId.generate()
    progress = Progress.record(
        progress_id=progress_id,
        user_id=user_id,
        progress_date=ProgressDate(date(2026, 1, 2)),
        unit=MeasurementUnit.METRIC,
        source=ProgressSource.MANUAL,
        clock=_CLOCK,
    )

    with session_factory() as session:
        ProgressSqlRepository(session).add(progress)
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        repository = ProgressSqlRepository(session)
        fetched = repository.get(progress_id)
        assert fetched is not None
        fetched.update_body_composition(clock=_CLOCK, body_weight=BodyWeight(80.0))
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        refetched = ProgressSqlRepository(session).get(progress_id)

    assert refetched is not None
    assert refetched.body_weight == BodyWeight(80.0)


@pytest.mark.integration
def test_list_by_user_returns_only_that_users_records(
    session_factory: sessionmaker[Session],
) -> None:
    user_a = _create_user(session_factory)
    user_b = _create_user(session_factory)

    for user_id in (user_a, user_a, user_b):
        progress = Progress.record(
            progress_id=ProgressId.generate(),
            user_id=user_id,
            progress_date=ProgressDate(date(2026, 1, 2)),
            unit=MeasurementUnit.METRIC,
            source=ProgressSource.MANUAL,
            clock=_CLOCK,
        )
        with session_factory() as session:
            ProgressSqlRepository(session).add(progress)
            session.commit()

    with session_factory() as session:
        records_for_a = ProgressSqlRepository(session).list_by_user(user_a)

    assert len(records_for_a) == 2
    assert all(record.user_id == user_a for record in records_for_a)


@pytest.mark.integration
def test_remove_deletes_the_row(session_factory: sessionmaker[Session]) -> None:
    user_id = _create_user(session_factory)
    progress_id = ProgressId.generate()
    progress = Progress.record(
        progress_id=progress_id,
        user_id=user_id,
        progress_date=ProgressDate(date(2026, 1, 2)),
        unit=MeasurementUnit.METRIC,
        source=ProgressSource.MANUAL,
        clock=_CLOCK,
    )

    with session_factory() as session:
        repository = ProgressSqlRepository(session)
        repository.add(progress)
        session.commit()
        repository.remove(progress)
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        assert ProgressSqlRepository(session).get(progress_id) is None
