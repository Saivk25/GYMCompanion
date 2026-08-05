"""Domain events raised by the `Credential` aggregate. See
`app.domain.shared_kernel.events`'s module docstring for the event
system's shape and the `kw_only=True` requirement every subclass here
follows.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class CredentialRegistered(DomainEvent):
    """A new login identity was created for a User. `email` is carried
    as a plain `str`, not an `Email` value object — an event is a
    record of what happened, read by whatever future subscriber cares
    (e.g. a welcome-email sender), and should not force every subscriber
    to import `app.domain.auth.value_objects` just to read a string.
    """

    user_id: UserId
    email: str


@dataclass(frozen=True, kw_only=True)
class TokensRevoked(DomainEvent):
    """Every refresh token previously issued for this Credential has
    been invalidated (logout, or a future "sign out everywhere"
    action) — see `Credential.revoke_tokens()`.
    """

    user_id: UserId
