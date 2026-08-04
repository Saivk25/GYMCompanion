"""Integration tests for `UserSqlRepository` against a real, migrated
Postgres database. See `tests/infra/conftest.py`'s `session_factory`
fixture — these tests skip themselves when no Postgres is reachable, the
same convention `tests/infra/test_migrations.py` already establishes.
"""

from datetime import datetime, time, timezone

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.domain.exercise.value_objects import EquipmentRequirement
from app.domain.shared_kernel.clock import FixedClock
from app.domain.user.enums import AccountStatus, BiologicalSex, ExperienceLevel
from app.domain.user.identifiers import UserId
from app.domain.user.user import User
from app.domain.user.value_objects import (
    AuthMethod,
    Locale,
    QuietHours,
    Timezone,
    UserPreferences,
    UserProfile,
)
from app.infra.repositories.user_repository import UserSqlRepository

_CLOCK = FixedClock(datetime(2026, 1, 1, tzinfo=timezone.utc))


@pytest.mark.integration
def test_add_and_get_round_trip(session_factory: sessionmaker[Session]) -> None:
    user_id = UserId.generate()
    user = User.register(
        user_id=user_id,
        locale=Locale("en-US"),
        timezone=Timezone("America/New_York"),
        auth_method=AuthMethod("webauthn_passkey"),
        clock=_CLOCK,
    )
    profile = UserProfile(
        height_cm=180.0,
        birth_year=1990,
        experience_level=ExperienceLevel.INTERMEDIATE,
        sex=BiologicalSex.MALE,
    )
    user.update_profile(profile, clock=_CLOCK)
    user.update_preferences(
        UserPreferences(
            quiet_hours=QuietHours(starts_at=time(22, 0), ends_at=time(7, 0)),
            biometric_app_lock_enabled=True,
            available_equipment=frozenset({EquipmentRequirement("barbell")}),
        )
    )

    with session_factory() as session:
        UserSqlRepository(session).add(user)
        session.commit()

    with session_factory() as session:
        fetched = UserSqlRepository(session).get(user_id)

    assert fetched is not None
    assert fetched.id == user_id
    assert fetched.locale == Locale("en-US")
    assert fetched.timezone == Timezone("America/New_York")
    assert fetched.profile == profile
    assert fetched.preferences.biometric_app_lock_enabled is True
    assert fetched.preferences.quiet_hours == QuietHours(starts_at=time(22, 0), ends_at=time(7, 0))
    assert fetched.preferences.available_equipment == frozenset({EquipmentRequirement("barbell")})


@pytest.mark.integration
def test_mutation_persists_without_a_second_add_call(
    session_factory: sessionmaker[Session],
) -> None:
    """The exact shape every mutating Application Layer handler relies on
    (e.g. `UpdateProfileHandler`): `get()`, mutate the returned aggregate
    through its own domain methods, `session.commit()` — no second
    `add()` call. See `app/infra/repositories/_tracking.py`'s module
    docstring for the mechanism that makes this work.
    """
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

    with session_factory() as session:
        repository = UserSqlRepository(session)
        fetched = repository.get(user_id)
        assert fetched is not None
        fetched.activate()
        session.commit()

    with session_factory() as session:
        refetched = UserSqlRepository(session).get(user_id)

    assert refetched is not None
    assert refetched.account_status is AccountStatus.ACTIVE


@pytest.mark.integration
def test_remove_deletes_the_row(session_factory: sessionmaker[Session]) -> None:
    user_id = UserId.generate()
    user = User.register(
        user_id=user_id,
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        auth_method=AuthMethod("password"),
        clock=_CLOCK,
    )

    with session_factory() as session:
        repository = UserSqlRepository(session)
        repository.add(user)
        session.commit()
        repository.remove(user)
        session.commit()

    with session_factory() as session:
        assert UserSqlRepository(session).get(user_id) is None


@pytest.mark.integration
def test_get_returns_none_for_unknown_id(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        assert UserSqlRepository(session).get(UserId.generate()) is None
