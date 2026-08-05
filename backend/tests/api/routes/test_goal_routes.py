"""End-to-end request tests for `app/api/routes/v1/goal.py` — all six
routes, using the `stub_client` fixture (`tests/api/conftest.py`) to
control exactly what `ApplicationResult` each route's handler
"returns", without a real database. This file is also where the
shared, module-agnostic error-mapping behaviors (`app/api/errors.py`)
get their most thorough exercise — `unwrap_or_400`/`unwrap_or_404`/
`unwrap_or_500`, `DomainInvariantViolationError` -> 422, and
`RequestValidationError` -> 422 all in one place — since every other
route module's own test file only needs to spot-check that its routes
wire the same shared helpers correctly, not re-prove the helpers
themselves.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.application.goal.dto.goal_dto import GoalDTO
from app.application.shared.application_result import ApplicationResult
from app.domain.goal.enums import GoalType
from app.domain.goal.identifiers import GoalId
from tests.application.goal.factories import a_created_goal

_VALID_CREATE_BODY = {
    "goal_type": GoalType.LOSE_FAT.value,
    "name": "Lose 5kg",
    "target_date": "2026-12-31",
}


def _goal_dto() -> GoalDTO:
    """A real `GoalDTO`, built from a real (in-memory, no repository
    involved) `Goal` aggregate via `a_created_goal()`
    (`tests/application/goal/factories.py`) and `GoalDTO.from_goal()` —
    reusing the Application Layer's own test factory instead of
    hand-constructing every one of `GoalDTO`'s many fields here, the
    same "don't re-derive what already exists" reasoning that applies
    to production code."""
    return GoalDTO.from_goal(a_created_goal())


@pytest.mark.unit
def test_create_goal_returns_201_and_id_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    goal_id = GoalId.generate()
    client = stub_client(ApplicationResult.ok(goal_id, warnings=("consider a smaller deficit",)))

    response = client.post("/api/v1/goals", json=_VALID_CREATE_BODY)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == str(goal_id)
    assert body["warnings"] == ["consider a smaller deficit"]


@pytest.mark.unit
def test_create_goal_returns_400_on_command_failure(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["user not found"]))

    response = client.post("/api/v1/goals", json=_VALID_CREATE_BODY)

    assert response.status_code == 400
    assert response.json()["detail"] == "user not found"


@pytest.mark.unit
def test_create_goal_collapses_multiple_errors_into_a_list(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["reason one", "reason two"]))

    response = client.post("/api/v1/goals", json=_VALID_CREATE_BODY)

    assert response.status_code == 400
    assert response.json()["detail"] == ["reason one", "reason two"]


@pytest.mark.unit
def test_create_goal_missing_required_field_returns_422(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.ok(GoalId.generate()))

    response = client.post("/api/v1/goals", json={})

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)


@pytest.mark.unit
def test_create_goal_with_domain_invalid_name_returns_422(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    """`name: ""` passes Pydantic's own `str` type check (this schema
    deliberately duplicates no length/emptiness rule — see `app/api/
    schemas/goal.py`'s module docstring) but fails `GoalName`'s own
    `__post_init__` inside the route's `body.to_command()` call, raising
    `DomainInvariantViolationError` before the stub handler is ever
    reached — proving the global exception handler
    (`app/api/errors.py`), not the route itself, is what produces this
    422.
    """
    client = stub_client(ApplicationResult.ok(GoalId.generate()))

    response = client.post("/api/v1/goals", json={**_VALID_CREATE_BODY, "name": ""})

    assert response.status_code == 422
    assert "workout name" not in response.json()["detail"]  # sanity: not a copy-paste error


@pytest.mark.unit
def test_get_goal_returns_200_and_the_full_resource_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    dto = _goal_dto()
    client = stub_client(ApplicationResult.ok(dto))

    response = client.get(f"/api/v1/goals/{dto.goal_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["goal_id"] == str(dto.goal_id)
    assert body["name"] == "Lose 5kg"
    assert body["status"] == "active"


@pytest.mark.unit
def test_get_goal_returns_404_when_not_found(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["goal ... not found"]))

    response = client.get(f"/api/v1/goals/{GoalId.generate()}")

    assert response.status_code == 404


@pytest.mark.unit
def test_get_goal_with_malformed_id_returns_422(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    """`GoalId.parse("not-a-uuid")` raises `ValueError` — not the domain
    layer's own `DomainInvariantViolationError` — inside the route
    function, ahead of the exception-handler-mapped cases. This proves
    the unhandled-exception path (a bare `ValueError`) also lands on the
    structured `ErrorResponse` envelope, at 500 — a malformed path
    parameter is arguably a client error, but `EntityId.parse()` raising
    a bare `ValueError` (see `app/domain/shared_kernel/identifiers.py`)
    isn't domain-invariant-shaped, so it isn't 422; this test documents
    the actual behavior rather than asserting a nicer one this phase
    doesn't implement.
    """
    client = stub_client(ApplicationResult.ok(_goal_dto()))

    response = client.get("/api/v1/goals/not-a-uuid")

    assert response.status_code == 500


@pytest.mark.unit
def test_list_goals_returns_200_and_every_dto_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    dtos = (_goal_dto(), _goal_dto())
    client = stub_client(ApplicationResult.ok(dtos))

    response = client.get("/api/v1/goals")

    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.unit
def test_list_goals_returns_500_on_failure(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["unexpected database error"]))

    response = client.get("/api/v1/goals")

    assert response.status_code == 500


@pytest.mark.unit
def test_update_goal_returns_200_and_id_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    goal_id = GoalId.generate()
    client = stub_client(ApplicationResult.ok(goal_id))

    response = client.patch(f"/api/v1/goals/{goal_id}", json={"priority": 2})

    assert response.status_code == 200
    assert response.json()["id"] == str(goal_id)


@pytest.mark.unit
def test_complete_goal_returns_200_and_id_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    goal_id = GoalId.generate()
    client = stub_client(ApplicationResult.ok(goal_id))

    response = client.post(f"/api/v1/goals/{goal_id}/complete")

    assert response.status_code == 200
    assert response.json()["id"] == str(goal_id)


@pytest.mark.unit
def test_complete_goal_returns_400_on_failure(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["goal is not Active"]))

    response = client.post(f"/api/v1/goals/{GoalId.generate()}/complete")

    assert response.status_code == 400


@pytest.mark.unit
def test_cancel_goal_returns_200_and_id_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    goal_id = GoalId.generate()
    client = stub_client(ApplicationResult.ok(goal_id))

    response = client.post(f"/api/v1/goals/{goal_id}/cancel")

    assert response.status_code == 200
    assert response.json()["id"] == str(goal_id)
