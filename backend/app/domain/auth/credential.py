"""The `Credential` aggregate root: one User's login identity.

Deliberately separate from `app.domain.user.User` — see the package
docstring (`app/domain/auth/__init__.py`) for why. `Credential.id` is
the same `UserId` the owning `User` uses, making the relationship a
strict one-to-one without a second, redundant identifier.
"""

from __future__ import annotations

from datetime import datetime

from app.domain.auth.enums import ROLE_PERMISSIONS, Permission, Role
from app.domain.auth.events import CredentialRegistered, TokensRevoked
from app.domain.auth.value_objects import Email, PasswordHash
from app.domain.shared_kernel.aggregate_root import AggregateRoot
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.validation import ensure
from app.domain.user.identifiers import UserId


class Credential(AggregateRoot[UserId]):
    """A User's login identity: the email they sign in with, their
    hashed password, their `Role`, and the token-revocation counter
    that backs `POST /logout`.

    Construct a brand-new credential via the `register()` factory,
    never `Credential(...)` directly — the constructor is also used to
    rehydrate an existing credential from a repository, where re-raising
    `CredentialRegistered` would be wrong (same convention as
    `app.domain.user.User`).
    """

    def __init__(
        self,
        credential_id: UserId,
        *,
        email: Email,
        password_hash: PasswordHash,
        role: Role = Role.MEMBER,
        token_version: int = 0,
        created_at: datetime,
    ) -> None:
        super().__init__(credential_id)
        ensure(created_at.tzinfo is not None, "created_at must be timezone-aware")
        ensure(token_version >= 0, "token_version must not be negative")
        self._email = email
        self._password_hash = password_hash
        self._role = role
        self._token_version = token_version
        self._created_at = created_at

    @classmethod
    def register(
        cls,
        *,
        user_id: UserId,
        email: Email,
        password_hash: PasswordHash,
        clock: Clock,
    ) -> Credential:
        """Creates a brand-new `Credential` for `user_id` and records
        `CredentialRegistered`. `password_hash` is already hashed —
        this factory (and this whole aggregate) never sees, and never
        could see, a plaintext password; hashing happens one layer up,
        via `app.domain.auth.ports.PasswordHasher`, before this is
        called (see `docs/adr/0032-authentication-and-authorization.md`).
        """
        registered_at = clock.now()
        credential = cls(
            user_id,
            email=email,
            password_hash=password_hash,
            role=Role.MEMBER,
            token_version=0,
            created_at=registered_at,
        )
        credential.record_event(
            CredentialRegistered(occurred_at=registered_at, user_id=user_id, email=email.value)
        )
        return credential

    @property
    def email(self) -> Email:
        return self._email

    @property
    def password_hash(self) -> PasswordHash:
        return self._password_hash

    @property
    def role(self) -> Role:
        return self._role

    @property
    def token_version(self) -> int:
        """Incremented every time every previously issued refresh token
        for this credential must stop working (`revoke_tokens()`). A
        refresh token embeds the `token_version` that was current when
        it was issued; `POST /refresh` rejects one whose embedded
        version no longer matches — the entire revocation strategy,
        with no second table and no external store. See
        `app.domain.auth.ports.TokenService`.
        """
        return self._token_version

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def revoke_tokens(self, *, clock: Clock) -> None:
        """Invalidates every refresh token issued for this credential
        so far (`POST /logout`) by advancing `token_version` — see that
        property's own docstring for the mechanism. Idempotent in
        effect (calling it twice just advances the counter twice, no
        different observable outcome than calling it once from a
        caller's perspective: either way, every token issued before
        *this* call stops working).
        """
        self._token_version += 1
        self.record_event(TokensRevoked(occurred_at=clock.now(), user_id=self.id))

    def has_permission(self, permission: Permission) -> bool:
        """Whether this credential's `role` grants `permission`, via
        `app.domain.auth.enums.ROLE_PERMISSIONS`. The one seam a future
        second role plugs into without this method's callers changing.
        """
        return permission in ROLE_PERMISSIONS.get(self._role, frozenset())
