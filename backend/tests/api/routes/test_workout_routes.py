"""End-to-end request tests for `app/api/routes/v1/workout.py` — all
ten routes (Workout + WorkoutSession), using the `stub_client` fixture
(`tests/api/conftest.py`). See `test_goal_routes.py`'s module docstring
for the shared testing strategy."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.application.shared.application_result import ApplicationResult
from app.application.workout.dto.workout_dto import WorkoutDTO
from app.application.workout.dto.workout_session_dto import WorkoutSessionDTO
from app.domain.exercise.identifiers import ExerciseId
from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout_session.identifiers import ExercisePerformanceId, WorkoutSessionId
from tests.application.workout.factories import a_planned_session, a_planned_workout

_VALID_CREATE_BODY = {
    "user_id": str(UserId.generate()),
    "name": "Push Day",
    "planned_date": "2026-06-01",
}


def _workout_dto() -> WorkoutDTO:
    return WorkoutDTO.from_workout(a_planned_workout())


def _session_dto() -> WorkoutSessionDTO:
    return WorkoutSessionDTO.from_workout_session(a_planned_session())


# ---------------------------------------------------------------------------
# Workout
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_create_workout_returns_201_and_id_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    workout_id = WorkoutId.generate()
    client = stub_client(ApplicationResult.ok(workout_id))

    response = client.post("/api/v1/workouts", json=_VALID_CREATE_BODY)

    assert response.status_code == 201
    assert response.json()["id"] == str(workout_id)


@pytest.mark.unit
def test_create_workout_returns_400_on_failure(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["user not found"]))

    response = client.post("/api/v1/workouts", json=_VALID_CREATE_BODY)

    assert response.status_code == 400


@pytest.mark.unit
def test_get_workout_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    dto = _workout_dto()
    client = stub_client(ApplicationResult.ok(dto))

    response = client.get(f"/api/v1/workouts/{dto.workout_id}")

    assert response.status_code == 200
    assert response.json()["workout_id"] == str(dto.workout_id)


@pytest.mark.unit
def test_get_workout_returns_404_when_not_found(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["not found"]))

    response = client.get(f"/api/v1/workouts/{WorkoutId.generate()}")

    assert response.status_code == 404


@pytest.mark.unit
def test_list_workouts_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.ok((_workout_dto(),)))

    response = client.get("/api/v1/workouts", params={"user_id": str(UserId.generate())})

    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.unit
def test_list_workouts_returns_500_on_failure(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["db error"]))

    response = client.get("/api/v1/workouts", params={"user_id": str(UserId.generate())})

    assert response.status_code == 500


@pytest.mark.unit
def test_update_workout_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    workout_id = WorkoutId.generate()
    client = stub_client(ApplicationResult.ok(workout_id))

    response = client.patch(f"/api/v1/workouts/{workout_id}", json={"goal": "hypertrophy"})

    assert response.status_code == 200
    assert response.json()["id"] == str(workout_id)


@pytest.mark.unit
def test_cancel_workout_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    workout_id = WorkoutId.generate()
    client = stub_client(ApplicationResult.ok(workout_id))

    response = client.post(f"/api/v1/workouts/{workout_id}/cancel")

    assert response.status_code == 200
    assert response.json()["id"] == str(workout_id)


@pytest.mark.unit
def test_cancel_workout_returns_400_on_failure(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["workout already cancelled"]))

    response = client.post(f"/api/v1/workouts/{WorkoutId.generate()}/cancel")

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# WorkoutSession
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_start_workout_session_returns_201_and_id_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    session_id = WorkoutSessionId.generate()
    client = stub_client(ApplicationResult.ok(session_id))

    response = client.post(
        f"/api/v1/workouts/{WorkoutId.generate()}/sessions",
        json={"session_date": "2026-06-01"},
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(session_id)


@pytest.mark.unit
def test_get_workout_session_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    dto = _session_dto()
    client = stub_client(ApplicationResult.ok(dto))

    response = client.get(f"/api/v1/workout-sessions/{dto.session_id}")

    assert response.status_code == 200
    assert response.json()["session_id"] == str(dto.session_id)


@pytest.mark.unit
def test_get_workout_session_returns_404_when_not_found(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["not found"]))

    response = client.get(f"/api/v1/workout-sessions/{WorkoutSessionId.generate()}")

    assert response.status_code == 404


@pytest.mark.unit
def test_complete_workout_session_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    session_id = WorkoutSessionId.generate()
    client = stub_client(ApplicationResult.ok(session_id))

    response = client.post(
        f"/api/v1/workout-sessions/{session_id}/complete",
        json={"duration_seconds": 3600, "completion_percentage": 100.0, "rating": 8},
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(session_id)


@pytest.mark.unit
def test_complete_workout_session_returns_400_on_failure(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.fail(["session is not Active"]))

    response = client.post(
        f"/api/v1/workout-sessions/{WorkoutSessionId.generate()}/complete",
        json={"duration_seconds": 3600, "completion_percentage": 100.0},
    )

    assert response.status_code == 400


@pytest.mark.unit
def test_log_exercise_set_returns_201_and_performance_id_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    performance_id = ExercisePerformanceId.generate()
    client = stub_client(ApplicationResult.ok(performance_id))

    response = client.post(
        f"/api/v1/workout-sessions/{WorkoutSessionId.generate()}/sets",
        json={
            "exercise_id": str(ExerciseId.generate()),
            "set_number": 1,
            "weight": 60.0,
            "reps": 10,
            "rpe": 7,
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(performance_id)


@pytest.mark.unit
def test_complete_exercise_set_returns_200_on_success(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    session_id = WorkoutSessionId.generate()
    client = stub_client(ApplicationResult.ok(session_id))

    response = client.post(
        f"/api/v1/workout-sessions/{session_id}/sets/complete",
        json={"performance_id": str(ExercisePerformanceId.generate()), "set_number": 1},
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(session_id)


@pytest.mark.unit
def test_complete_exercise_set_missing_required_field_returns_422(
    stub_client: Callable[[ApplicationResult[Any]], TestClient],
) -> None:
    client = stub_client(ApplicationResult.ok(WorkoutSessionId.generate()))

    response = client.post(
        f"/api/v1/workout-sessions/{WorkoutSessionId.generate()}/sets/complete", json={}
    )

    assert response.status_code == 422
