"""`GetUserHandler`: fetches one User's current state as a `UserDTO`.

A read-side handler needs no `Clock` and no `DomainEventDispatcher` —
it never mutates an aggregate or raises a domain event — and never
calls `UnitOfWork.commit()`: nothing was staged for persistence, so
there is nothing to make durable. It still runs inside `with
self._uow:` for the same resource-lifecycle reasons a command handler
does (a concrete implementation may hold a database session open for
the duration), and it still translates a repository-level failure into
a failed `ApplicationResult` — reading can fail for infrastructure
reasons just as writing can.
"""

from __future__ import annotations

from app.application.shared.application_result import ApplicationResult
from app.application.shared.query_handler import QueryHandler
from app.application.shared.unit_of_work import UnitOfWork
from app.application.user.dto.user_dto import UserDTO
from app.application.user.queries.get_user import GetUserQuery
from app.domain.user.repository import UserRepository
from app.domain.user.user import User


class GetUserHandler(QueryHandler[GetUserQuery, UserDTO]):
    """Loads a User and returns it as a `UserDTO`, or a failed
    `ApplicationResult` if no such user exists."""

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, request: GetUserQuery) -> ApplicationResult[UserDTO]:
        # `user` is initialized before the `try` (not inside it) so it is
        # always definitely assigned below — see the identical reasoning
        # in the mutating handlers (e.g. `update_profile_handler.py`).
        user: User | None = None
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
                user = repository.get(request.user_id)
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        if user is None:
            return ApplicationResult.fail([f"user {request.user_id} not found"])

        return ApplicationResult.ok(UserDTO.from_user(user))
