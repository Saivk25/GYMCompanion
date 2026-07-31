"""`UpdatePreferencesCommand`: the input to `UpdatePreferencesHandler`.

Same reasoning as `UpdateProfileCommand` — carries a complete
`UserPreferences` value object, not its individual fields, so the
handler never reconstructs or re-validates one.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.user.identifiers import UserId
from app.domain.user.value_objects import UserPreferences


@dataclass(frozen=True, kw_only=True)
class UpdatePreferencesCommand(Command):
    """Replace an existing User's preferences."""

    user_id: UserId
    preferences: UserPreferences
