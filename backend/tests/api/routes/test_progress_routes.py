"""End-to-end request tests for `app/api/routes/v1/progress.py` — all
seven routes, using the `stub_client` fixture (`tests/api/conftest.py`).
See `test_goal_routes.py`'s module docstring for the shared testing
strategy."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.application.progress.dto.progress_dto import ProgressDTO
from app.application.shared.application_result import ApplicationResult
from app.domain.progress.identifiers import ProgressId
from app.domain.user.identifiers import UserId
from tests.application.progress.factories import a_recorded_progress

_VALID_RECORD_BODY = {
    "user_id": str(UserId.generate()),
    "progress_date": "2026-06-01",
    "unit": "metric",
    "source": "manual",
    "body_weight": 80.0,
}


def _progress_dto() -> ProgressDTO:
    return ProgressDTO.from_progress(a_recorded_progress())


@pytest.mark.unit
def test_record_progress_returns_201_and_id_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    progress_id = ProgressId.generate()
    client = stub_client(ApplicationResult.ok(progress_id))

    response = client.post("/api/v1/progress", json=_VALID_RECORD_BODY)

    assert response.status_code == 201
    assert response.json()["id"] == str(progress_id)


@pytest.mark.unit
def test_record_progress_returns_400_on_failure(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["user not found"]))

    response = client.post("/api/v1/progress", json=_VALID_RECORD_BODY)

    assert response.status_code == 400


@pytest.mark.unit
def test_get_progress_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    dto = _progress_dto()
    client = stub_client(ApplicationResult.ok(dto))

    response = client.get(f"/api/v1/progress/{dto.progress_id}")

    assert response.status_code == 200
    assert response.json()["progress_id"] == str(dto.progress_id)


@pytest.mark.unit
def test_get_progress_returns_404_when_not_found(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["not found"]))

    response = client.get(f"/api/v1/progress/{ProgressId.generate()}")

    assert response.status_code == 404


@pytest.mark.unit
def test_list_progress_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.ok((_progress_dto(),)))

    response = client.get("/api/v1/progress", params={"user_id": str(UserId.generate())})

    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.unit
def test_list_progress_returns_500_on_failure(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["db error"]))

    response = client.get("/api/v1/progress", params={"user_id": str(UserId.generate())})

    assert response.status_code == 500


@pytest.mark.unit
def test_update_body_composition_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    progress_id = ProgressId.generate()
    client = stub_client(ApplicationResult.ok(progress_id))

    response = client.put(
        f"/api/v1/progress/{progress_id}/body-composition", json={"body_weight": 79.5}
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(progress_id)


@pytest.mark.unit
def test_update_measurements_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    progress_id = ProgressId.generate()
    client = stub_client(ApplicationResult.ok(progress_id))

    response = client.put(f"/api/v1/progress/{progress_id}/measurements", json={"waist": 80.0})

    assert response.status_code == 200
    assert response.json()["id"] == str(progress_id)


@pytest.mark.unit
def test_update_progress_notes_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    progress_id = ProgressId.generate()
    client = stub_client(ApplicationResult.ok(progress_id))

    response = client.put(f"/api/v1/progress/{progress_id}/notes", json={"notes": "feeling good"})

    assert response.status_code == 200
    assert response.json()["id"] == str(progress_id)


@pytest.mark.unit
def test_update_progress_notes_missing_required_field_returns_422(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    progress_id = ProgressId.generate()
    client = stub_client(ApplicationResult.ok(progress_id))

    response = client.put(f"/api/v1/progress/{progress_id}/notes", json={})

    assert response.status_code == 422


@pytest.mark.unit
def test_delete_progress_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    progress_id = ProgressId.generate()
    client = stub_client(ApplicationResult.ok(progress_id))

    response = client.delete(f"/api/v1/progress/{progress_id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(progress_id)


@pytest.mark.unit
def test_delete_progress_returns_400_on_failure(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["already deleted"]))

    response = client.delete(f"/api/v1/progress/{ProgressId.generate()}")

    assert response.status_code == 400
