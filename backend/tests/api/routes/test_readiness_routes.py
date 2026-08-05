"""End-to-end request tests for `app/api/routes/v1/readiness.py` — all
seven routes, using the `stub_client` fixture (`tests/api/conftest.py`).
See `test_goal_routes.py`'s module docstring for the shared testing
strategy."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.application.readiness.dto.readiness_dto import ReadinessDTO
from app.application.shared.application_result import ApplicationResult
from app.domain.readiness.identifiers import ReadinessId
from app.domain.user.identifiers import UserId
from tests.application.readiness.factories import a_recorded_readiness

_VALID_RECORD_BODY = {
    "user_id": str(UserId.generate()),
    "readiness_date": "2026-06-01",
    "sleep_quality": 7,
}


def _readiness_dto() -> ReadinessDTO:
    return ReadinessDTO.from_readiness(a_recorded_readiness())


@pytest.mark.unit
def test_record_readiness_returns_201_and_id_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    readiness_id = ReadinessId.generate()
    client = stub_client(ApplicationResult.ok(readiness_id))

    response = client.post("/api/v1/readiness", json=_VALID_RECORD_BODY)

    assert response.status_code == 201
    assert response.json()["id"] == str(readiness_id)


@pytest.mark.unit
def test_record_readiness_returns_400_on_failure(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["user not found"]))

    response = client.post("/api/v1/readiness", json=_VALID_RECORD_BODY)

    assert response.status_code == 400


@pytest.mark.unit
def test_get_readiness_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    dto = _readiness_dto()
    client = stub_client(ApplicationResult.ok(dto))

    response = client.get(f"/api/v1/readiness/{dto.readiness_id}")

    assert response.status_code == 200
    assert response.json()["readiness_id"] == str(dto.readiness_id)


@pytest.mark.unit
def test_get_readiness_returns_404_when_not_found(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["not found"]))

    response = client.get(f"/api/v1/readiness/{ReadinessId.generate()}")

    assert response.status_code == 404


@pytest.mark.unit
def test_list_readiness_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.ok((_readiness_dto(),)))

    response = client.get("/api/v1/readiness", params={"user_id": str(UserId.generate())})

    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.unit
def test_list_readiness_returns_500_on_failure(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["db error"]))

    response = client.get("/api/v1/readiness", params={"user_id": str(UserId.generate())})

    assert response.status_code == 500


@pytest.mark.unit
def test_update_sleep_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    readiness_id = ReadinessId.generate()
    client = stub_client(ApplicationResult.ok(readiness_id))

    response = client.put(
        f"/api/v1/readiness/{readiness_id}/sleep",
        json={"sleep_duration_seconds": 25200, "sleep_quality": 8},
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(readiness_id)


@pytest.mark.unit
def test_update_recovery_metrics_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    readiness_id = ReadinessId.generate()
    client = stub_client(ApplicationResult.ok(readiness_id))

    response = client.put(
        f"/api/v1/readiness/{readiness_id}/recovery-metrics", json={"energy_level": 6}
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(readiness_id)


@pytest.mark.unit
def test_update_readiness_notes_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    readiness_id = ReadinessId.generate()
    client = stub_client(ApplicationResult.ok(readiness_id))

    response = client.put(f"/api/v1/readiness/{readiness_id}/notes", json={"notes": "rested"})

    assert response.status_code == 200
    assert response.json()["id"] == str(readiness_id)


@pytest.mark.unit
def test_update_readiness_notes_missing_required_field_returns_422(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    readiness_id = ReadinessId.generate()
    client = stub_client(ApplicationResult.ok(readiness_id))

    response = client.put(f"/api/v1/readiness/{readiness_id}/notes", json={})

    assert response.status_code == 422


@pytest.mark.unit
def test_delete_readiness_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    readiness_id = ReadinessId.generate()
    client = stub_client(ApplicationResult.ok(readiness_id))

    response = client.delete(f"/api/v1/readiness/{readiness_id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(readiness_id)


@pytest.mark.unit
def test_delete_readiness_returns_400_on_failure(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["already deleted"]))

    response = client.delete(f"/api/v1/readiness/{ReadinessId.generate()}")

    assert response.status_code == 400
