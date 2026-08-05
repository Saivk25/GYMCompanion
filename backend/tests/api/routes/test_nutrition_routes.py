"""End-to-end request tests for `app/api/routes/v1/nutrition.py` — all
seven routes, using the `stub_client` fixture (`tests/api/conftest.py`).
See `test_goal_routes.py`'s module docstring for the shared testing
strategy this file (and every other route module's own test file)
follows; shared error-mapping behaviors are proven thoroughly there and
only spot-checked here.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.application.nutrition.dto.nutrition_dto import NutritionDTO
from app.application.shared.application_result import ApplicationResult
from app.domain.nutrition.identifiers import NutritionId
from tests.application.nutrition.factories import a_recorded_nutrition

_VALID_RECORD_BODY = {
    "nutrition_date": "2026-06-01",
    "calories": 500,
}


def _nutrition_dto() -> NutritionDTO:
    return NutritionDTO.from_nutrition(a_recorded_nutrition())


@pytest.mark.unit
def test_record_nutrition_returns_201_and_id_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    nutrition_id = NutritionId.generate()
    client = stub_client(ApplicationResult.ok(nutrition_id))

    response = client.post("/api/v1/nutrition", json=_VALID_RECORD_BODY)

    assert response.status_code == 201
    assert response.json()["id"] == str(nutrition_id)


@pytest.mark.unit
def test_record_nutrition_returns_400_on_failure(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["user not found"]))

    response = client.post("/api/v1/nutrition", json=_VALID_RECORD_BODY)

    assert response.status_code == 400


@pytest.mark.unit
def test_get_nutrition_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    dto = _nutrition_dto()
    client = stub_client(ApplicationResult.ok(dto))

    response = client.get(f"/api/v1/nutrition/{dto.nutrition_id}")

    assert response.status_code == 200
    assert response.json()["nutrition_id"] == str(dto.nutrition_id)


@pytest.mark.unit
def test_get_nutrition_returns_404_when_not_found(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["not found"]))

    response = client.get(f"/api/v1/nutrition/{NutritionId.generate()}")

    assert response.status_code == 404


@pytest.mark.unit
def test_list_nutrition_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.ok((_nutrition_dto(),)))

    response = client.get("/api/v1/nutrition")

    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.unit
def test_list_nutrition_returns_500_on_failure(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["db error"]))

    response = client.get("/api/v1/nutrition")

    assert response.status_code == 500


@pytest.mark.unit
def test_update_nutrition_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    nutrition_id = NutritionId.generate()
    client = stub_client(ApplicationResult.ok(nutrition_id))

    response = client.patch(f"/api/v1/nutrition/{nutrition_id}", json={"calories": 600})

    assert response.status_code == 200
    assert response.json()["id"] == str(nutrition_id)


@pytest.mark.unit
def test_update_water_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    nutrition_id = NutritionId.generate()
    client = stub_client(ApplicationResult.ok(nutrition_id))

    response = client.put(f"/api/v1/nutrition/{nutrition_id}/water", json={"water_intake": 1.5})

    assert response.status_code == 200
    assert response.json()["id"] == str(nutrition_id)


@pytest.mark.unit
def test_update_water_missing_required_field_returns_422(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    nutrition_id = NutritionId.generate()
    client = stub_client(ApplicationResult.ok(nutrition_id))

    response = client.put(f"/api/v1/nutrition/{nutrition_id}/water", json={})

    assert response.status_code == 422


@pytest.mark.unit
def test_update_nutrition_notes_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    nutrition_id = NutritionId.generate()
    client = stub_client(ApplicationResult.ok(nutrition_id))

    response = client.put(f"/api/v1/nutrition/{nutrition_id}/notes", json={"notes": "felt good"})

    assert response.status_code == 200
    assert response.json()["id"] == str(nutrition_id)


@pytest.mark.unit
def test_delete_nutrition_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    nutrition_id = NutritionId.generate()
    client = stub_client(ApplicationResult.ok(nutrition_id))

    response = client.delete(f"/api/v1/nutrition/{nutrition_id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(nutrition_id)


@pytest.mark.unit
def test_delete_nutrition_returns_400_on_failure(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["already deleted"]))

    response = client.delete(f"/api/v1/nutrition/{NutritionId.generate()}")

    assert response.status_code == 400
