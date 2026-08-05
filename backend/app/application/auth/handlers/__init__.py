"""Concrete `CommandHandler`/`QueryHandler` implementations for the
Authentication Application Use Cases. Same load/mutate-or-verify/
commit/dispatch shape every other handler in this codebase follows
(see `app.application.user.handlers`'s own package docstring) — the
only new collaborators any handler here adds are
`app.domain.auth.ports.PasswordHasher` and `...TokenService`, both
resolved generically by `app.composition.container.Container.handler()`
the same way `dispatcher`/`clock` already are.
"""

from app.application.auth.handlers.get_current_user_handler import GetCurrentUserHandler
from app.application.auth.handlers.login_handler import LoginHandler
from app.application.auth.handlers.logout_handler import LogoutHandler
from app.application.auth.handlers.refresh_handler import RefreshHandler
from app.application.auth.handlers.register_handler import RegisterHandler

__all__ = [
    "GetCurrentUserHandler",
    "LoginHandler",
    "LogoutHandler",
    "RefreshHandler",
    "RegisterHandler",
]
