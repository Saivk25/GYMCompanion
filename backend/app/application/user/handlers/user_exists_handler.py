"""`UserExistsHandler`: checks whether a User with a given id exists.

Unlike `GetUserHandler`, "no such user" is not a failure here — it is
a successful `False`. Only a genuine repository-level failure (an
exception from `repository.get(...)`) produces a failed
`ApplicationResult`. See `queries/user_exists.py`'s module docstring
for why this is a distinct query/handler rather than a thin wrapper
around `GetUserQuery`/`GetUserHandler`.
"""

from __future__ import annotations

from app.application.shared.application_result import ApplicationResult
from app.application.shared.query_handler import QueryHandler
from app.application.shared.unit_of_work import UnitOfWork
from app.application.user.queries.user_exists import UserExistsQuery
from app.domain.user.repository import UserRepository


class UserExistsHandler(QueryHandler[UserExistsQuery, bool]):
    """Reports whether a User with `request.user_id` exists."""

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, request: UserExistsQuery) -> ApplicationResult[bool]:
        # `exists` is initialized before the `try` for the same
        # definite-assignment reasoning as `GetUserHandler.handle`.
        exists = False
        try:
            with self._uow as uow:
                # UserRepository has no concrete implementation in this phase
                # (by design); mypy's type-abstract check assumes a type[T]
                # argument might be instantiated, but get_repository only ever
                # uses it as a lookup key, so this is a documented, narrow
                # false positive.
                repository = uow.get_repository(
                    UserRepository  # type: ignore[type-abstract]
                )
                exists = repository.get(request.user_id) is not None
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        return ApplicationResult.ok(exists)
