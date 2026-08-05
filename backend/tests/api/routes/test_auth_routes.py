"""End-to-end request tests for `app/api/routes/auth.py` — all five
Authentication routes, using the `stub_client` fixture
(`tests/api/conftest.py`). See `test_goal_routes.py`'s module docstring
for the shared testing strategy this file follows; `get_current_user_id`
is already overridden by `stub_client` to a fixed `UserId`
(`authenticated_user_id`), so `logout`/`me` need no bearer token of
their own here — `tests/api/test_deps.py` is where that dependency's
own behavior (missing/invalid/expired token) is proven.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.application.auth.dto.auth_tokens_dto import AuthTokensDTO
from app.application.auth.dto.current_user_dto import CurrentUserDTO
from app.application.shared.application_result import ApplicationResult
from app.domain.auth.enums import Role
from app.domain.auth.value_objects import Email
from app.domain.user.enums import AccountStatus
from app.domain.user.identifiers import UserId
from app.domain.user.value_objects import Locale, Timezone

_VALID_REGISTER_BODY = {
    "email": "sai@example.com",
    "password": "correct horse battery staple",
    "locale": "en",
    "timezone": "UTC",
}

_VALID_LOGIN_BODY = {"email": "sai@example.com", "password": "correct horse battery staple"}


def _tokens_dto() -> AuthTokensDTO:
    return AuthTokensDTO(
        access_token="an-access-token", refresh_token="a-refresh-token", expires_in=900
    )


def _current_user_dto(user_id: UserId) -> CurrentUserDTO:
    return CurrentUserDTO(
        user_id=user_id,
        email=Email("sai@example.com"),
        role=Role.MEMBER,
        account_status=AccountStatus.ACTIVE,
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


# --- register ---


@pytest.mark.unit
def test_register_returns_201_and_tokens_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.ok(_tokens_dto()))

    response = client.post("/register", json=_VALID_REGISTER_BODY)

    assert response.status_code == 201
    body = response.json()
    assert body["access_token"] == "an-access-token"
    assert body["refresh_token"] == "a-refresh-token"
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 900


@pytest.mark.unit
def test_register_returns_400_when_email_already_registered(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["email already registered"]))

    response = client.post("/register", json=_VALID_REGISTER_BODY)

    assert response.status_code == 400
    assert response.json()["detail"] == "email already registered"


@pytest.mark.unit
def test_register_missing_required_field_returns_422(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.ok(_tokens_dto()))

    response = client.post("/register", json={"email": "sai@example.com"})

    assert response.status_code == 422


# --- login ---


@pytest.mark.unit
def test_login_returns_200_and_tokens_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.ok(_tokens_dto()))

    response = client.post("/login", json=_VALID_LOGIN_BODY)

    assert response.status_code == 200
    assert response.json()["access_token"] == "an-access-token"


@pytest.mark.unit
def test_login_returns_401_on_invalid_credentials(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    """Proves `login` uses `unwrap_or_401`, not `unwrap_or_400` — a
    wrong password is "unauthorized," not an ordinary bad request. See
    `app/api/errors.py`'s module docstring."""
    client = stub_client(ApplicationResult.fail(["invalid email or password"]))

    response = client.post("/login", json=_VALID_LOGIN_BODY)

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid email or password"


# --- refresh ---


@pytest.mark.unit
def test_refresh_returns_200_and_new_tokens_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.ok(_tokens_dto()))

    response = client.post("/refresh", json={"refresh_token": "a-refresh-token"})

    assert response.status_code == 200
    assert response.json()["refresh_token"] == "a-refresh-token"


@pytest.mark.unit
def test_refresh_returns_401_when_token_was_revoked(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["refresh token has been revoked"]))

    response = client.post("/refresh", json={"refresh_token": "a-stale-refresh-token"})

    assert response.status_code == 401


@pytest.mark.unit
def test_refresh_missing_required_field_returns_422(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.ok(_tokens_dto()))

    response = client.post("/refresh", json={})

    assert response.status_code == 422


# --- logout ---


@pytest.mark.unit
def test_logout_returns_204_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
    authenticated_user_id: UserId,
) -> None:
    client = stub_client(ApplicationResult.ok(authenticated_user_id))

    response = client.post("/logout")

    assert response.status_code == 204
    assert response.content == b""


@pytest.mark.unit
def test_logout_returns_400_when_credential_not_found(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["credential ... not found"]))

    response = client.post("/logout")

    assert response.status_code == 400


# --- me ---


@pytest.mark.unit
def test_me_returns_200_and_the_callers_own_identity(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
    authenticated_user_id: UserId,
) -> None:
    dto = _current_user_dto(authenticated_user_id)
    client = stub_client(ApplicationResult.ok(dto))

    response = client.get("/me")

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == str(authenticated_user_id)
    assert body["email"] == "sai@example.com"
    assert body["role"] == "member"


@pytest.mark.unit
def test_me_returns_404_when_the_account_no_longer_exists(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["user ... not found"]))

    response = client.get("/me")

    assert response.status_code == 404
