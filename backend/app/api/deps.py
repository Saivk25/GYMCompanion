"""FastAPI dependency wiring — the one place any route reaches into the
Composition Root.

Three dependencies routes in this API use:

- `get_container` reads the process-lifetime `Container` FastAPI's own
  `lifespan` (`app/main.py`) built once at startup and stored on
  `app.state.container`.
- `handler_dependency(handler_type)` is a factory returning a
  per-request FastAPI dependency that resolves a fresh instance of
  exactly the one handler type a given route needs — "fresh", not
  cached, because `Container.handler()` itself is designed to never be
  cached (see that method's own docstring): each call also constructs a
  brand-new `SqlAlchemyUnitOfWork`, which is what gives every request
  its own request-scoped `UnitOfWork` with no risk of two concurrent
  requests racing on a shared session.
- `get_current_user_id` is the authentication gate every protected
  route (every existing `v1` route, per this phase's own directive, plus
  `GET /me` and `POST /logout` in `app/api/routes/auth.py`) declares as
  a dependency. It reads the `Authorization: Bearer <token>` header via
  FastAPI's `HTTPBearer` security scheme — chosen specifically because
  declaring it as a dependency is also what makes FastAPI emit a
  `securitySchemes: {bearerAuth: {type: http, scheme: bearer}}` block in
  the generated OpenAPI document, with a padlock icon on every route
  that depends on it, satisfying this phase's own "OpenAPI security
  definitions" verification item with no separate, hand-written schema
  needed — then decodes it via `container.token_service.
  decode_access_token`, translating `InvalidTokenError`/
  `ExpiredTokenError` (`app.domain.auth.ports`) into a `401` the same
  `ErrorResponse` envelope every other failure in this API uses (see
  `app/api/errors.py`'s module docstring), rather than either exception
  type ever reaching a route body or the global `Exception` handler.

No route ever imports `app.composition.Container` and calls
`.handler()` itself — routing every handler resolution through this one
module is what keeps "dependency injection everywhere" (this phase's
own rule) enforceable by a single import-boundary test
(`tests/api/test_import_boundaries.py`) rather than by convention alone.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.shared.interfaces import Handler
from app.composition.container import Container
from app.domain.auth.ports import ExpiredTokenError, InvalidTokenError
from app.domain.user.identifiers import UserId

H = TypeVar("H", bound=Handler[Any, Any])

_bearer_scheme = HTTPBearer(
    scheme_name="bearerAuth",
    description="A JWT access token issued by POST /login, POST /register, or POST /refresh.",
)

# Not a credential — a human-readable error message, the same documented
# false positive `app.application.auth.dto.auth_tokens_dto.AuthTokensDTO.
# token_type` already carries a noqa for.
_INVALID_TOKEN_DETAIL = "invalid or expired access token"  # noqa: S105


def get_container(request: Request) -> Container:
    """Returns the `Container` FastAPI's lifespan built once at process
    startup. Never constructs one itself — `Container.validate()` (run
    once, inside `bootstrap()`) exercises the whole dependency graph, so
    a `Container` is meant to be built exactly once per process, not
    once per request.
    """
    container: Container = request.app.state.container
    return container


def handler_dependency(handler_type: type[H]) -> Callable[[Container], H]:
    """Builds a FastAPI dependency that resolves a fresh `handler_type`
    instance via the request-scoped `Container`, on every request.

    Usage, in a route module: `_get_create_goal_handler =
    handler_dependency(CreateGoalHandler)`, then `handler:
    CreateGoalHandler = Depends(_get_create_goal_handler)` as a route
    parameter — the same shape every route in this API uses to obtain
    its one handler, with no per-route boilerplate beyond naming the
    handler type.
    """

    def _resolve(container: Container = Depends(get_container)) -> H:  # noqa: B008 — FastAPI's own DI pattern
        return container.handler(handler_type)

    return _resolve


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),  # noqa: B008
    container: Container = Depends(get_container),  # noqa: B008
) -> UserId:
    """Decodes the bearer token's access-token claims and returns the
    caller's `UserId` — the one piece of identity every protected route
    actually needs (a route wanting the full profile depends on
    `GetCurrentUserHandler` instead, the same way `GET /me` does; see
    `app/api/routes/auth.py`).

    Deliberately returns `UserId`, not `AccessTokenClaims` — a route
    depending on this only ever needs "who is calling", never the raw
    claims object, and returning the narrower type keeps every other
    route module free of any reason to import `app.domain.auth` at all
    (see `tests/api/test_import_boundaries.py`).
    """
    try:
        claims = container.token_service.decode_access_token(credentials.credentials)
    except (InvalidTokenError, ExpiredTokenError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_INVALID_TOKEN_DETAIL,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return claims.user_id
