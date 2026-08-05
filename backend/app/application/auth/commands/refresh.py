"""`RefreshCommand`: the input to `RefreshHandler`."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command


@dataclass(frozen=True, kw_only=True)
class RefreshCommand(Command):
    """Exchange a still-valid, not-yet-revoked refresh token for a
    fresh pair of tokens. `refresh_token` is the raw encoded JWT
    string — not a domain value object, the same reasoning
    `RefreshTokenClaims` (`app.domain.auth.ports`) gives for staying a
    plain dataclass: decoding and validating it is
    `TokenService.decode_refresh_token`'s job, not something this
    command does itself.
    """

    refresh_token: str
