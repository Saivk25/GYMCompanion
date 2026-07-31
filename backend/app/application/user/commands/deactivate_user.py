"""`DeactivateUserCommand`: the input to `DeactivateUserHandler`.

"Deactivate" maps to `User.suspend()` (Active -> Suspended), not
`User.delete()` — a deliberate reading of an otherwise domain-silent
term (the Bible names the state `Suspended`, not `Deactivated`; see
`app.domain.user.enums.AccountStatus`). Suspension is reversible via
the same `User.activate()` that also handles Invited -> Active
(`user.py`'s own docstring on why one method covers both), matching
what "deactivate" means in most account-management UIs: a temporary,
reversible hold, not the permanent, escalation-gated `delete()`. See
`docs/adr/0023-user-application-use-cases.md` for the full reasoning.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class DeactivateUserCommand(Command):
    """Suspend an existing, currently-Active User."""

    user_id: UserId
