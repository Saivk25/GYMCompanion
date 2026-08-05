"""`GetCurrentUserHandler`: fetches the authenticated caller's own
identity as a `CurrentUserDTO` (`GET /me`).

Loads both `User` and `Credential` — the same aggregate pair
`RegisterHandler` creates together — through their own repositories,
inside one `UnitOfWork`, and combines them via `CurrentUserDTO.
from_user_and_credential`. Read-only, so no `Clock` and no
`DomainEventDispatcher`, matching `GetUserHandler`'s own reasoning.
"""

from __future__ import annotations

from app.application.auth.dto.current_user_dto import CurrentUserDTO
from app.application.auth.queries.get_current_user import GetCurrentUserQuery
from app.application.shared.application_result import ApplicationResult
from app.application.shared.query_handler import QueryHandler
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.auth.credential import Credential
from app.domain.auth.repository import CredentialRepository
from app.domain.user.repository import UserRepository
from app.domain.user.user import User


class GetCurrentUserHandler(QueryHandler[GetCurrentUserQuery, CurrentUserDTO]):
    """Loads the caller's `User` + `Credential` and returns them as one
    `CurrentUserDTO`, or a failed `ApplicationResult` if either is
    missing (a caller with a validly signed token for a since-deleted
    account, which `RefreshHandler`'s own revocation check does not by
    itself prevent for an access token still inside its short TTL)."""

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, request: GetCurrentUserQuery) -> ApplicationResult[CurrentUserDTO]:
        user: User | None = None
        credential: Credential | None = None
        try:
            with self._uow as uow:
                user_repository = uow.get_repository(
                    UserRepository  # type: ignore[type-abstract]
                )
                credential_repository = uow.get_repository(
                    CredentialRepository  # type: ignore[type-abstract]
                )
                user = user_repository.get(request.user_id)
                credential = credential_repository.get(request.user_id)
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        if user is None or credential is None:
            return ApplicationResult.fail([f"user {request.user_id} not found"])

        return ApplicationResult.ok(CurrentUserDTO.from_user_and_credential(user, credential))
