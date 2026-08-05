"""HTTP routes for Authentication — five endpoints, one per Application
Handler in `app.application.auth.handlers`.

| Method | Path      | Handler                | Auth required |
|--------|-----------|-------------------------|----------------|
| POST   | /register | RegisterHandler          | no             |
| POST   | /login    | LoginHandler              | no             |
| POST   | /refresh  | RefreshHandler            | no (bears its own token) |
| POST   | /logout   | LogoutHandler             | yes            |
| GET    | /me       | GetCurrentUserHandler     | yes            |

Root-level, unprefixed (no `/api/v1`) — the same placement
`app/api/routes/health.py` already established, and matching the
directive's own literal endpoint list (`POST /register`, not `POST
/api/v1/register`).

Same three-step shape every other route in this API follows (see
`app/api/routes/v1/goal.py`'s module docstring): convert the request via
a schema's `to_command()`, resolve the one handler needed via
`handler_dependency`, and convert the `ApplicationResult` via one of
`app.api.errors`'s `unwrap_or_*` helpers. `logout` and `me` additionally
depend on `get_current_user_id` — the only two routes in this module
that need to know who is calling rather than being handed a credential
to check.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user_id, handler_dependency
from app.api.errors import unwrap_or_400, unwrap_or_401, unwrap_or_404
from app.api.schemas.auth import (
    CurrentUserResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.application.auth.commands.logout import LogoutCommand
from app.application.auth.handlers.get_current_user_handler import GetCurrentUserHandler
from app.application.auth.handlers.login_handler import LoginHandler
from app.application.auth.handlers.logout_handler import LogoutHandler
from app.application.auth.handlers.refresh_handler import RefreshHandler
from app.application.auth.handlers.register_handler import RegisterHandler
from app.application.auth.queries.get_current_user import GetCurrentUserQuery
from app.domain.user.identifiers import UserId

router = APIRouter(tags=["auth"])

_get_register_handler = handler_dependency(RegisterHandler)
_get_login_handler = handler_dependency(LoginHandler)
_get_refresh_handler = handler_dependency(RefreshHandler)
_get_logout_handler = handler_dependency(LogoutHandler)
_get_current_user_handler = handler_dependency(GetCurrentUserHandler)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    body: RegisterRequest, handler: RegisterHandler = Depends(_get_register_handler)
) -> TokenResponse:
    result = handler.handle(body.to_command())
    return TokenResponse.from_dto(unwrap_or_400(result))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, handler: LoginHandler = Depends(_get_login_handler)) -> TokenResponse:
    result = handler.handle(body.to_command())
    return TokenResponse.from_dto(unwrap_or_401(result))


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    body: RefreshRequest, handler: RefreshHandler = Depends(_get_refresh_handler)
) -> TokenResponse:
    result = handler.handle(body.to_command())
    return TokenResponse.from_dto(unwrap_or_401(result))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def logout(
    user_id: UserId = Depends(get_current_user_id),
    handler: LogoutHandler = Depends(_get_logout_handler),
) -> None:
    result = handler.handle(LogoutCommand(user_id=user_id))
    unwrap_or_400(result)


@router.get("/me", response_model=CurrentUserResponse)
def me(
    user_id: UserId = Depends(get_current_user_id),
    handler: GetCurrentUserHandler = Depends(_get_current_user_handler),
) -> CurrentUserResponse:
    result = handler.handle(GetCurrentUserQuery(user_id=user_id))
    return CurrentUserResponse.from_dto(unwrap_or_404(result))
