"""`UpdateEquipmentCommand`: the input to `UpdateEquipmentHandler`.

A distinct, single-purpose command from `UpdatePreferencesCommand`
even though both ultimately target
`User.preferences.available_equipment` — "update the equipment I own"
is a common, standalone user action (e.g. a dedicated "My equipment"
screen) worth its own command rather than forcing every equipment edit
through a full-preferences replacement. See `User.update_equipment()`
(`app.domain.user.user`) for why the aggregate itself exposes a
matching narrow method, and
`docs/adr/0023-user-application-use-cases.md` for why "equipment"
lives on `UserPreferences` at all rather than a separate
`EnvironmentContext` aggregate.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.exercise.value_objects import EquipmentRequirement
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class UpdateEquipmentCommand(Command):
    """Replace the equipment an existing User has told the app they
    own or regularly have access to."""

    user_id: UserId
    available_equipment: frozenset[EquipmentRequirement]
