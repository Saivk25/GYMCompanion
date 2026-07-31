"""Concrete `CommandHandler`/`QueryHandler` implementations for the
User Application Use Cases. See
`docs/adr/0023-user-application-use-cases.md` for the shape every
handler here follows: load through a repository interface, invoke
aggregate behavior, commit the `UnitOfWork`, dispatch domain events
only after a successful commit, return an `ApplicationResult` — never
a business rule of the handler's own.
"""

from app.application.user.handlers.create_user_handler import CreateUserHandler
from app.application.user.handlers.deactivate_user_handler import DeactivateUserHandler
from app.application.user.handlers.get_user_handler import GetUserHandler
from app.application.user.handlers.update_equipment_handler import UpdateEquipmentHandler
from app.application.user.handlers.update_preferences_handler import UpdatePreferencesHandler
from app.application.user.handlers.update_profile_handler import UpdateProfileHandler
from app.application.user.handlers.user_exists_handler import UserExistsHandler

__all__ = [
    "CreateUserHandler",
    "DeactivateUserHandler",
    "GetUserHandler",
    "UpdateEquipmentHandler",
    "UpdatePreferencesHandler",
    "UpdateProfileHandler",
    "UserExistsHandler",
]
