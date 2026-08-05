"""`CurrentUserDTO`: the shape `GetCurrentUserHandler` (`GET /me`)
returns — a read-only projection combining the two aggregates a caller's
identity is actually split across (`app.domain.auth.Credential` and
`app.domain.user.User`), so a caller of `GET /me` gets one coherent
response instead of needing to know that split exists.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from app.domain.auth.enums import Role
from app.domain.auth.value_objects import Email
from app.domain.user.enums import AccountStatus
from app.domain.user.identifiers import UserId
from app.domain.user.value_objects import Locale, Timezone

if TYPE_CHECKING:
    from app.domain.auth.credential import Credential
    from app.domain.user.user import User


@dataclass(frozen=True, kw_only=True)
class CurrentUserDTO:
    """An immutable, read-only snapshot of the authenticated caller's
    own identity, taken at query time."""

    user_id: UserId
    email: Email
    role: Role
    account_status: AccountStatus
    locale: Locale
    timezone: Timezone
    created_at: datetime

    @classmethod
    def from_user_and_credential(cls, user: User, credential: Credential) -> CurrentUserDTO:
        """Builds a DTO from a live `User` + its `Credential` — the two
        aggregates `GetCurrentUserHandler` loads separately (each
        through its own repository) and combines here, once, rather
        than leaving that combination to every caller."""
        return cls(
            user_id=user.id,
            email=credential.email,
            role=credential.role,
            account_status=user.account_status,
            locale=user.locale,
            timezone=user.timezone,
            created_at=user.created_at,
        )
