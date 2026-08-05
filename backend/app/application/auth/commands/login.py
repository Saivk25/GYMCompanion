"""`LoginCommand`: the input to `LoginHandler`. See `register.py`'s own
docstring for why `password` stays a plain `str`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.auth.value_objects import Email


@dataclass(frozen=True, kw_only=True)
class LoginCommand(Command):
    """Exchange an email + password for a fresh pair of tokens."""

    email: Email
    password: str
