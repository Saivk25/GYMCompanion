"""Full-stack integration tests for Authentication & Authorization — the
real `register` -> `login` -> `refresh` -> `logout` flow, and a real
protected `v1` route, against an actually-migrated Postgres database via
`live_migrated_client` (`tests/api/conftest.py`). Every other test in
`tests/api/` proves routing/mapping against a stub; this file is the one
place a request travels all the way through `RegisterHandler` ->
`bcrypt`/PyJWT -> `SqlAlchemyUnitOfWork` -> Postgres and back, satisfying
this phase's own "Full integration tests" verification item.

Skips itself (see `live_migrated_client`'s own docstring) when no
Postgres is reachable, the same convention every other `@pytest.mark.
integration` test in this codebase already follows — these are not
expected to run in every environment, but are expected to run in CI.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient

_A_PASSWORD = "correct horse battery staple"


def _register(client: TestClient, *, email: str, password: str = _A_PASSWORD) -> dict[str, Any]:
    response = client.post(
        "/register",
        json={"email": email, "password": password, "locale": "en", "timezone": "UTC"},
    )
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


@pytest.mark.integration
def test_register_returns_a_usable_token_pair(live_migrated_client: TestClient) -> None:
    email = f"{uuid.uuid4()}@example.com"

    tokens = _register(live_migrated_client, email=email)

    assert tokens["token_type"] == "bearer"
    assert tokens["expires_in"] > 0
    assert tokens["access_token"]
    assert tokens["refresh_token"]


@pytest.mark.integration
def test_registering_the_same_email_twice_returns_400(live_migrated_client: TestClient) -> None:
    email = f"{uuid.uuid4()}@example.com"
    _register(live_migrated_client, email=email)

    response = live_migrated_client.post(
        "/register",
        json={"email": email, "password": _A_PASSWORD, "locale": "en", "timezone": "UTC"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "email already registered"


@pytest.mark.integration
def test_me_returns_the_registered_identity(live_migrated_client: TestClient) -> None:
    email = f"{uuid.uuid4()}@example.com"
    tokens = _register(live_migrated_client, email=email)

    response = live_migrated_client.get("/me", headers=_auth_headers(tokens["access_token"]))

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == email
    assert body["role"] == "member"


@pytest.mark.integration
def test_login_with_correct_credentials_returns_a_fresh_token_pair(
    live_migrated_client: TestClient,
) -> None:
    email = f"{uuid.uuid4()}@example.com"
    _register(live_migrated_client, email=email)

    response = live_migrated_client.post("/login", json={"email": email, "password": _A_PASSWORD})

    assert response.status_code == 200
    assert response.json()["access_token"]


@pytest.mark.integration
def test_login_with_wrong_password_returns_401(live_migrated_client: TestClient) -> None:
    email = f"{uuid.uuid4()}@example.com"
    _register(live_migrated_client, email=email)

    response = live_migrated_client.post("/login", json={"email": email, "password": "wrong"})

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid email or password"


@pytest.mark.integration
def test_login_with_unregistered_email_returns_the_same_401_as_wrong_password(
    live_migrated_client: TestClient,
) -> None:
    """Account-enumeration defense, proven end to end — see
    `LoginHandler`'s own module docstring."""
    response = live_migrated_client.post(
        "/login", json={"email": f"{uuid.uuid4()}@example.com", "password": _A_PASSWORD}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid email or password"


@pytest.mark.integration
def test_refresh_rotates_the_refresh_token(live_migrated_client: TestClient) -> None:
    email = f"{uuid.uuid4()}@example.com"
    tokens = _register(live_migrated_client, email=email)

    response = live_migrated_client.post(
        "/refresh", json={"refresh_token": tokens["refresh_token"]}
    )

    assert response.status_code == 200
    rotated = response.json()
    assert rotated["refresh_token"] != tokens["refresh_token"]
    assert rotated["access_token"]


@pytest.mark.integration
def test_refresh_with_a_garbage_token_returns_401(live_migrated_client: TestClient) -> None:
    response = live_migrated_client.post("/refresh", json={"refresh_token": "not-a-real-token"})

    assert response.status_code == 401


@pytest.mark.integration
def test_logout_revokes_the_refresh_token(live_migrated_client: TestClient) -> None:
    email = f"{uuid.uuid4()}@example.com"
    tokens = _register(live_migrated_client, email=email)

    logout_response = live_migrated_client.post(
        "/logout", headers=_auth_headers(tokens["access_token"])
    )
    assert logout_response.status_code == 204

    refresh_response = live_migrated_client.post(
        "/refresh", json={"refresh_token": tokens["refresh_token"]}
    )

    assert refresh_response.status_code == 401


@pytest.mark.integration
def test_protected_route_rejects_a_request_with_no_bearer_token(
    live_migrated_client: TestClient,
) -> None:
    response = live_migrated_client.post(
        "/api/v1/goals",
        json={"goal_type": "lose_fat", "name": "Lose 5kg", "target_date": "2026-12-31"},
    )

    assert response.status_code == 403


@pytest.mark.integration
def test_protected_route_rejects_a_garbage_bearer_token(live_migrated_client: TestClient) -> None:
    response = live_migrated_client.post(
        "/api/v1/goals",
        json={"goal_type": "lose_fat", "name": "Lose 5kg", "target_date": "2026-12-31"},
        headers=_auth_headers("not-a-real-token"),
    )

    assert response.status_code == 401


@pytest.mark.integration
def test_authenticated_caller_can_create_and_then_list_their_own_goal(
    live_migrated_client: TestClient,
) -> None:
    """Proves the create-goal route now derives `user_id` from the
    authenticated caller (`app/api/schemas/goal.py`'s `CreateGoalRequest`
    no longer accepts one) rather than from client-supplied input —
    creating a goal with no `user_id` in the body, then listing goals
    with no `user_id` query param, and getting the created goal back."""
    email = f"{uuid.uuid4()}@example.com"
    tokens = _register(live_migrated_client, email=email)
    headers = _auth_headers(tokens["access_token"])

    create_response = live_migrated_client.post(
        "/api/v1/goals",
        json={"goal_type": "lose_fat", "name": "Lose 5kg", "target_date": "2026-12-31"},
        headers=headers,
    )
    assert create_response.status_code == 201, create_response.text
    goal_id = create_response.json()["id"]

    list_response = live_migrated_client.get("/api/v1/goals", headers=headers)

    assert list_response.status_code == 200
    assert any(goal["goal_id"] == goal_id for goal in list_response.json())
