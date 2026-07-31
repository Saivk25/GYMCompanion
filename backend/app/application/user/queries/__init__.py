"""Immutable query objects for the User Application Use Cases."""

from app.application.user.queries.get_user import GetUserQuery
from app.application.user.queries.user_exists import UserExistsQuery

__all__ = ["GetUserQuery", "UserExistsQuery"]
