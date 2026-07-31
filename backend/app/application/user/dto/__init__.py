"""Read-only transport objects for the User Application Use Cases.

Currently one: `UserDTO` — the shape `GetUserHandler` returns. See
`user_dto.py` for why this is a distinct type from
`app.domain.user.context.UserContext` rather than a reuse of it.
"""

from app.application.user.dto.user_dto import UserDTO

__all__ = ["UserDTO"]
