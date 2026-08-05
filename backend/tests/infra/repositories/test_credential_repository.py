"""Integration tests for `CredentialSqlRepository` against a real,
migrated Postgres database. See `test_user_repository.py`'s module
docstring for the shared fixture convention.

Every test here creates the matching `User` row first (`credentials.
user_id` is a foreign key to `users.user_id` — see
`app/infra/models/credential.py`), the same order `RegisterHandler`
itself always uses.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.domain.auth.credential import Credential
from app.domain.auth.value_objects import Email, PasswordHash
from app.domain.shared_kernel.clock import FixedClock
from app.domain.user.identifiers import UserId
from app.domain.user.user import User
from app.domain.user.value_objects import AuthMethod, Locale, Timezone
from app.infra.repositories.credential_repository import CredentialSqlRepository
from app.infra.repositories.user_repository import UserSqlRepository

_CLOCK = FixedClock(datetime(2026, 1, 1, tzinfo=timezone.utc))


def _add_matching_user(session: Session, user_id: UserId) -> None:
    user = User.register(
        user_id=user_id,
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        auth_method=AuthMethod("password"),
        clock=_CLOCK,
    )
    UserSqlRepository(session).add(user)


@pytest.mark.integration
def test_add_and_get_round_trip(session_factory: sessionmaker[Session]) -> None:
    user_id = UserId.generate()
    credential = Credential.register(
        user_id=user_id,
        email=Email("sai@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
        clock=_CLOCK,
    )

    with session_factory() as session:
        _add_matching_user(session, user_id)
        CredentialSqlRepository(session).add(credential)
        session.commit()

    with session_factory() as session:
        fetched = CredentialSqlRepository(session).get(user_id)

    assert fetched is not None
    assert fetched.email == Email("sai@example.com")
    assert fetched.token_version == 0


@pytest.mark.integration
def test_get_by_email_finds_the_matching_credential(
    session_factory: sessionmaker[Session],
) -> None:
    user_id = UserId.generate()
    credential = Credential.register(
        user_id=user_id,
        email=Email("get-by-email@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
        clock=_CLOCK,
    )

    with session_factory() as session:
        _add_matching_user(session, user_id)
        CredentialSqlRepository(session).add(credential)
        session.commit()

    with session_factory() as session:
        fetched = CredentialSqlRepository(session).get_by_email(Email("get-by-email@example.com"))

    assert fetched is not None
    assert fetched.id == user_id


@pytest.mark.integration
def test_get_by_email_returns_none_for_an_unregistered_email(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        fetched = CredentialSqlRepository(session).get_by_email(Email("nobody@example.com"))

    assert fetched is None


@pytest.mark.integration
def test_mutation_persists_without_a_second_add_call(
    session_factory: sessionmaker[Session],
) -> None:
    """`revoke_tokens()` (a plain in-place mutation, no second `add()`
    call) must still persist — the same `TrackingRepository` guarantee
    every other repository in this package already relies on."""
    user_id = UserId.generate()
    credential = Credential.register(
        user_id=user_id,
        email=Email("revoke@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
        clock=_CLOCK,
    )

    with session_factory() as session:
        _add_matching_user(session, user_id)
        CredentialSqlRepository(session).add(credential)
        session.commit()

    with session_factory() as session:
        repository = CredentialSqlRepository(session)
        fetched = repository.get(user_id)
        assert fetched is not None
        fetched.revoke_tokens(clock=_CLOCK)
        session.commit()

    with session_factory() as session:
        refetched = CredentialSqlRepository(session).get(user_id)

    assert refetched is not None
    assert refetched.token_version == 1


@pytest.mark.integration
def test_remove_deletes_the_row(session_factory: sessionmaker[Session]) -> None:
    user_id = UserId.generate()
    credential = Credential.register(
        user_id=user_id,
        email=Email("remove@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
        clock=_CLOCK,
    )

    with session_factory() as session:
        _add_matching_user(session, user_id)
        repository = CredentialSqlRepository(session)
        repository.add(credential)
        session.commit()
        repository.remove(credential)
        session.commit()

    with session_factory() as session:
        assert CredentialSqlRepository(session).get(user_id) is None


@pytest.mark.integration
def test_duplicate_email_is_rejected_by_the_unique_constraint(
    session_factory: sessionmaker[Session],
) -> None:
    first_user_id = UserId.generate()
    second_user_id = UserId.generate()
    shared_email = Email("duplicate@example.com")

    with session_factory() as session:
        _add_matching_user(session, first_user_id)
        CredentialSqlRepository(session).add(
            Credential.register(
                user_id=first_user_id,
                email=shared_email,
                password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
                clock=_CLOCK,
            )
        )
        session.commit()

    with (
        pytest.raises(Exception, match=r"(?i)unique|duplicate"),
        session_factory() as session,
    ):
        _add_matching_user(session, second_user_id)
        CredentialSqlRepository(session).add(
            Credential.register(
                user_id=second_user_id,
                email=shared_email,
                password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
                clock=_CLOCK,
            )
        )
        session.commit()
