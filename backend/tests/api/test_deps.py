"""Tests for `app.api.deps.get_current_user_id` — the bearer-token
authentication gate every protected route in this API depends on (see
that function's own docstring, and `app/api/routes/auth.py`'s module
docstring for which routes use it).

Exercised through a real `TestClient` request to `GET /me` (rather than
calling the dependency function directly) so these tests prove the
actual wiring FastAPI performs — `HTTPBearer`'s own "no Authorization
header" behavior, the dependency's own `InvalidTokenError`/
`ExpiredTokenError` -> 401 mapping, and a successful decode reaching the
route — not just the function body in isolation. `get_container` is
overridden with a small stub exposing a real `FakeTokenService`
(`tests.application.auth.factories`) as `token_service` and a
`GetCurrentUserHandler`-shaped stub as `handler()`, matching this
package's own `stub_client` pattern (`conftest.py`) rather than a real
database.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_container
from app.application.auth.dto.current_user_dto import CurrentUserDTO
from app.application.shared.application_result import ApplicationResult
from app.domain.auth.enums import Role
from app.domain.auth.value_objects import Email
from app.domain.user.enums import AccountStatus
from app.domain.user.identifiers import UserId
from app.domain.user.value_objects import Locale, Timezone
from app.main import create_app
from tests.application.auth.factories import FakeTokenService

_A_VALID_TOKEN = "access:11111111-1111-4111-8111-111111111111:member"
_AN_INVALID_TOKEN = "not-a-real-token"
_AN_EXPIRED_TOKEN = "access:11111111-1111-4111-8111-111111111111:member:expired"


class _StubHandler:
    def __init__(self, result: ApplicationResult[Any]) -> None:
        self._result = result

    def handle(self, request: object) -> ApplicationResult[Any]:
        del request
        return self._result


class _StubContainerWithTokenService:
    """A `get_container` override exposing a real `FakeTokenService` as
    `token_service` — everything `get_current_user_id` itself touches —
    plus a `handler()` that always resolves to a fixed, successful
    `GetCurrentUserHandler` result, so a valid token's request can reach
    `GET /me` end to end without a real database."""

    def __init__(self, token_service: FakeTokenService, dto: CurrentUserDTO) -> None:
        self.token_service = token_service
        self._dto = dto

    def handler(self, handler_type: type) -> _StubHandler:
        del handler_type
        return _StubHandler(ApplicationResult.ok(self._dto))


def _a_current_user_dto() -> CurrentUserDTO:
    return CurrentUserDTO(
        user_id=UserId.parse("11111111-1111-4111-8111-111111111111"),
        email=Email("sai@example.com"),
        role=Role.MEMBER,
        account_status=AccountStatus.ACTIVE,
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def _client(token_service: FakeTokenService) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_container] = lambda: _StubContainerWithTokenService(
        token_service, _a_current_user_dto()
    )
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.unit
def test_valid_bearer_token_reaches_the_route() -> None:
    client = _client(FakeTokenService())

    response = client.get("/me", headers={"Authorization": f"Bearer {_A_VALID_TOKEN}"})

    assert response.status_code == 200
    assert response.json()["user_id"] == "11111111-1111-4111-8111-111111111111"


@pytest.mark.unit
def test_missing_authorization_header_is_rejected() -> None:
    client = _client(FakeTokenService())

    response = client.get("/me")

    # HTTPBearer's own default behavior for "no Authorization header at
    # all" is 403, not 401 — distinct from "a header was present but the
    # token inside it was rejected" (both cases below). Documented here
    # as the actual, verified behavior rather than an assumption.
    assert response.status_code == 403


@pytest.mark.unit
def test_invalid_token_returns_401() -> None:
    client = _client(FakeTokenService(invalid_tokens=frozenset({_AN_INVALID_TOKEN})))

    response = client.get("/me", headers={"Authorization": f"Bearer {_AN_INVALID_TOKEN}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid or expired access token"
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.unit
def test_expired_token_returns_401() -> None:
    client = _client(FakeTokenService(expired_tokens=frozenset({_AN_EXPIRED_TOKEN})))

    response = client.get("/me", headers={"Authorization": f"Bearer {_AN_EXPIRED_TOKEN}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid or expired access token"


@pytest.mark.unit
def test_malformed_authorization_scheme_is_rejected() -> None:
    """`Authorization: Basic ...` (not `Bearer`) — `HTTPBearer` itself
    rejects this before `get_current_user_id`'s own body ever runs."""
    client = _client(FakeTokenService())

    response = client.get("/me", headers={"Authorization": f"Basic {_A_VALID_TOKEN}"})

    assert response.status_code == 403
