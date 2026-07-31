"""Immutable command objects for the User Application Use Cases — one
per write operation `app/application/user/handlers/` implements. See
each module for the reasoning behind its specific shape.
"""

from app.application.user.commands.create_user import CreateUserCommand
from app.application.user.commands.deactivate_user import DeactivateUserCommand
from app.application.user.commands.update_equipment import UpdateEquipmentCommand
from app.application.user.commands.update_preferences import UpdatePreferencesCommand
from app.application.user.commands.update_profile import UpdateProfileCommand

__all__ = [
    "CreateUserCommand",
    "DeactivateUserCommand",
    "UpdateEquipmentCommand",
    "UpdatePreferencesCommand",
    "UpdateProfileCommand",
]
