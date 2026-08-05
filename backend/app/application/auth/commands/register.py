"""`RegisterCommand`: the input to `RegisterHandler`.

`email`/`locale`/`timezone` are already the domain value objects that
validate their own format — the same convention every other module's
command carries (e.g. `CreateGoalCommand`'s `GoalName`). `password` is
deliberately a plain `str`, not `app.domain.auth.value_objects.
PasswordHash`: a `PasswordHash` can only be produced by hashing, and
hashing is `RegisterHandler`'s own job (via the injected
`PasswordHasher`), not something the API layer or this command can do
first — see `docs/adr/0032-authentication-and-authorization.md`,
"No password handling outside Authentication services."
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.auth.value_objects import Email
from app.domain.user.value_objects import Locale, Timezone


@dataclass(frozen=True, kw_only=True)
class RegisterCommand(Command):
    """Register a brand-new User and its login `Credential`."""

    email: Email
    password: str
    locale: Locale
    timezone: Timezone
