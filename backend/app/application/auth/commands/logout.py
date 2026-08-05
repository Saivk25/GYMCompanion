"""`LogoutCommand`: the input to `LogoutHandler`."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class LogoutCommand(Command):
    """Revoke every refresh token issued to `user_id` so far.
    `user_id` comes from the caller's already-validated access token
    (the API layer's authenticated-user dependency), never from a
    request body — a caller cannot log another user out."""

    user_id: UserId
