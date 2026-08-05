"""Shared test doubles and helpers for the Authentication Application
Use Cases' test suite. Not itself a test file (no `test_` prefix). See
`tests/application/user/factories.py`'s own docstring for the general
reasoning — every fake here follows the identical shape, extended to
cover the two aggregates (`User` + `Credential`) and two security
collaborators (`PasswordHasher`, `TokenService`) this package's
handlers use that `app.application.user`'s never did.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any

from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.auth.credential import Credential
from app.domain.auth.enums import Role
from app.domain.auth.ports import (
    AccessTokenClaims,
    ExpiredTokenError,
    InvalidTokenError,
    PasswordHasher,
    RefreshTokenClaims,
    TokenService,
)
from app.domain.auth.repository import CredentialRepository
from app.domain.auth.value_objects import Email, PasswordHash
from app.domain.shared_kernel.clock import FixedClock
from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.identifiers import UserId
from app.domain.user.repository import UserRepository
from app.domain.user.user import User

_A_FIXED_INSTANT = datetime(2026, 1, 1, tzinfo=timezone.utc)
_ACCESS_TOKEN_TTL_SECONDS = 900


def a_fixed_clock() -> FixedClock:
    """A `FixedClock` pinned to an arbitrary, fixed instant — see
    `tests/domain/auth/factories.py`'s identical helper."""
    return FixedClock(_A_FIXED_INSTANT)


class FakeCredentialRepository(CredentialRepository):
    """An in-memory `CredentialRepository`. See
    `tests.application.user.factories.FakeUserRepository`'s identical
    `fail_on_*` reasoning."""

    def __init__(
        self,
        credentials: dict[UserId, Credential] | None = None,
        *,
        fail_on_get: bool = False,
        fail_on_add: bool = False,
    ) -> None:
        self._credentials: dict[UserId, Credential] = dict(credentials) if credentials else {}
        self.fail_on_get = fail_on_get
        self.fail_on_add = fail_on_add
        self.added: list[Credential] = []
        self.removed: list[Credential] = []

    def get(self, entity_id: UserId) -> Credential | None:
        if self.fail_on_get:
            raise RuntimeError("repository unavailable")
        return self._credentials.get(entity_id)

    def add(self, aggregate: Credential) -> None:
        if self.fail_on_add:
            raise ValueError(f"credential {aggregate.id} already exists")
        self.added.append(aggregate)
        self._credentials[aggregate.id] = aggregate

    def remove(self, aggregate: Credential) -> None:
        self.removed.append(aggregate)
        self._credentials.pop(aggregate.id, None)

    def get_by_email(self, email: Email) -> Credential | None:
        if self.fail_on_get:
            raise RuntimeError("repository unavailable")
        return next((c for c in self._credentials.values() if c.email == email), None)


class FakeUnitOfWork(UnitOfWork):
    """An in-memory `UnitOfWork` scoped to one `FakeUserRepository`-like
    object and/or one `FakeCredentialRepository` — a handler in this
    package may need either, or both (`RegisterHandler`,
    `GetCurrentUserHandler`), so this fake resolves whichever of the
    two repository types it was constructed with, matching
    `SqlAlchemyUnitOfWork.get_repository`'s own type-keyed lookup
    shape. `fail_on_commit` simulates `commit()` itself failing.
    """

    def __init__(
        self,
        *,
        user_repository: UserRepository | None = None,
        credential_repository: CredentialRepository | None = None,
        fail_on_commit: bool = False,
    ) -> None:
        self.user_repository = user_repository
        self.credential_repository = credential_repository
        self.fail_on_commit = fail_on_commit
        self.committed = False
        self.rolled_back = False
        self.commit_calls = 0
        self.rollback_calls = 0

    def commit(self) -> None:
        if self.fail_on_commit:
            raise RuntimeError("commit failed")
        self.committed = True
        self.commit_calls += 1

    def rollback(self) -> None:
        self.rolled_back = True
        self.rollback_calls += 1

    def get_repository(self, repository_type: type[Any]) -> Any:
        if repository_type is UserRepository and self.user_repository is not None:
            return self.user_repository
        if repository_type is CredentialRepository and self.credential_repository is not None:
            return self.credential_repository
        raise KeyError(repository_type)  # pragma: no cover — no other repo type is asked for


class RecordingDispatcher(DomainEventDispatcher):
    """A `DomainEventDispatcher` that records every event it was asked
    to dispatch, in order — see
    `tests.application.user.factories.RecordingDispatcher`."""

    def __init__(self) -> None:
        self.dispatched: list[DomainEvent] = []

    def dispatch(self, events: Sequence[DomainEvent]) -> None:
        self.dispatched.extend(events)


class OrderTrackingDispatcher(DomainEventDispatcher):
    """See `tests.application.user.factories.OrderTrackingDispatcher`
    — identical shape, appends `"dispatch"` to a shared `call_order`
    list."""

    def __init__(self, call_order: list[str]) -> None:
        self._call_order = call_order
        self.dispatched: list[DomainEvent] = []

    def dispatch(self, events: Sequence[DomainEvent]) -> None:
        self._call_order.append("dispatch")
        self.dispatched.extend(events)


class OrderTrackingUnitOfWork(FakeUnitOfWork):
    """A `FakeUnitOfWork` that appends to a shared `call_order` list on
    every `commit()`/`rollback()` — see `OrderTrackingDispatcher`."""

    def __init__(
        self,
        call_order: list[str],
        *,
        user_repository: UserRepository | None = None,
        credential_repository: CredentialRepository | None = None,
        fail_on_commit: bool = False,
    ) -> None:
        super().__init__(
            user_repository=user_repository,
            credential_repository=credential_repository,
            fail_on_commit=fail_on_commit,
        )
        self._call_order = call_order

    def commit(self) -> None:
        super().commit()
        self._call_order.append("commit")

    def rollback(self) -> None:
        super().rollback()
        self._call_order.append("rollback")


class FakePasswordHasher(PasswordHasher):
    """A deterministic, obviously-not-real `PasswordHasher` — prefixes
    the plaintext rather than running any real algorithm, which is
    exactly right for a test double whose only job is proving
    `RegisterHandler`/`LoginHandler` call `hash()`/`verify()` at all,
    never to exercise bcrypt's own correctness (that belongs to
    `tests/infra/security/test_bcrypt_password_hasher.py`).
    """

    def hash(self, plain_password: str) -> PasswordHash:
        return PasswordHash(f"fake-hash:{plain_password}")

    def verify(self, plain_password: str, password_hash: PasswordHash) -> bool:
        return password_hash.value == f"fake-hash:{plain_password}"


class FakeTokenService(TokenService):
    """A deterministic, obviously-not-real `TokenService`. `invalid_tokens`
    and `expired_tokens` let a test make a specific token string decode
    to a specific failure, without needing a real JWT library or a real
    clock advancing past a real expiry."""

    def __init__(
        self,
        *,
        invalid_tokens: frozenset[str] = frozenset(),
        expired_tokens: frozenset[str] = frozenset(),
    ) -> None:
        self._invalid_tokens = invalid_tokens
        self._expired_tokens = expired_tokens
        self._issuance_counter = 0
        self.issued_access_tokens: list[tuple[UserId, Role]] = []
        self.issued_refresh_tokens: list[tuple[UserId, int]] = []

    @property
    def access_token_ttl_seconds(self) -> int:
        return _ACCESS_TOKEN_TTL_SECONDS

    def issue_access_token(self, *, user_id: UserId, role: Role) -> str:
        self.issued_access_tokens.append((user_id, role))
        return f"access:{user_id}:{role.value}"

    def issue_refresh_token(self, *, user_id: UserId, token_version: int) -> str:
        # A real JWT differs on every issuance even for identical claims
        # (iat/jti). `_issuance_counter` reproduces that here, in a fake
        # simple enough to otherwise be fully deterministic, so a test
        # can assert refresh-token rotation actually changes the string.
        self._issuance_counter += 1
        self.issued_refresh_tokens.append((user_id, token_version))
        return f"refresh:{user_id}:{token_version}:{self._issuance_counter}"

    def decode_access_token(self, token: str) -> AccessTokenClaims:
        self._check_token(token)
        _, user_id, role = token.split(":")
        return AccessTokenClaims(user_id=UserId.parse(user_id), role=Role(role))

    def decode_refresh_token(self, token: str) -> RefreshTokenClaims:
        self._check_token(token)
        # maxsplit=3, and only the first three parts are used: a token
        # this fake issued itself carries a trailing ":<issuance>" (see
        # issue_refresh_token above); a token a test constructs by hand
        # (`f"refresh:{user_id}:0"`) does not, and both must decode the
        # same way.
        parts = token.split(":", 3)
        _, user_id, token_version = parts[0], parts[1], parts[2]
        return RefreshTokenClaims(user_id=UserId.parse(user_id), token_version=int(token_version))

    def _check_token(self, token: str) -> None:
        if token in self._expired_tokens:
            raise ExpiredTokenError(f"token expired: {token!r}")
        if token in self._invalid_tokens:
            raise InvalidTokenError(f"invalid token: {token!r}")


def a_registered_user(*, user_id: UserId) -> User:
    """A minimal, already-registered `User` for handler tests that need
    one to exist without exercising `User.register()`'s own behavior
    (already covered by `tests/domain/user/test_user.py`)."""
    from app.domain.user.value_objects import AuthMethod, Locale, Timezone

    return User.register(
        user_id=user_id,
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        auth_method=AuthMethod("password"),
        clock=a_fixed_clock(),
    )


def a_registered_credential(*, user_id: UserId, email: str = "sai@example.com") -> Credential:
    """A minimal, already-registered `Credential` — see
    `a_registered_user`'s identical reasoning."""
    return Credential.register(
        user_id=user_id,
        email=Email(email),
        password_hash=PasswordHash("fake-hash:correct horse battery staple"),
        clock=a_fixed_clock(),
    )
