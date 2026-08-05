"""`AuthTokensDTO`: the shape `RegisterHandler`, `LoginHandler`, and
`RefreshHandler` all return — a fresh, usable pair of tokens.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class AuthTokensDTO:
    """An immutable snapshot of one freshly issued token pair.
    `token_type` is always `"bearer"` — carried as data, not hard-coded
    a second time in the API layer's response schema, so the two can
    never drift (see `docs/adr/0032-authentication-and-authorization.md`
    for why Bearer tokens, not cookies)."""

    access_token: str
    refresh_token: str
    expires_in: int
    # Not a credential — the RFC 6750 constant naming the token scheme
    # ("Bearer"), not a secret value. Ruff's bandit rule (S105) flags any
    # string literal assigned to a field whose name contains "token" on
    # sight, the same documented false positive `app.core.config.
    # Settings._PLACEHOLDER_SECRET_KEY` already carries a noqa for.
    token_type: str = "bearer"  # noqa: S105
