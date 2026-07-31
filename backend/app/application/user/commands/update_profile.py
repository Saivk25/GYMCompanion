"""`UpdateProfileCommand`: the input to `UpdateProfileHandler`.

Carries a complete, already-valid `UserProfile` rather than its
individual fields — `UserProfile` is a `ValueObject` (Domain Layer):
it validates itself once at construction (`__post_init__`), so a
`CreateUserCommand`-style flat-fields shape here would only invite the
handler to reconstruct a `UserProfile` from parts, duplicating
validation the value object already owns. The handler's only job is to
hand this profile to `User.update_profile(...)` unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.user.identifiers import UserId
from app.domain.user.value_objects import UserProfile


@dataclass(frozen=True, kw_only=True)
class UpdateProfileCommand(Command):
    """Replace an existing User's profile."""

    user_id: UserId
    profile: UserProfile
