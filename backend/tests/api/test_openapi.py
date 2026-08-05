"""Proves the fully-wired app actually generates a valid OpenAPI schema
and registers every route this phase's task list names — "OpenAPI
generation" and "Route registration" from the phase's own VERIFICATION
section, each as an executed property rather than an assumption.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI

# One route entry per endpoint this phase implements — (method, path) —
# independent of `app/api/routes/v1/*.py`'s own source so this test
# would actually fail if a route were accidentally dropped, renamed, or
# never registered, rather than just re-deriving the same list from the
# same place and trivially matching it.
_EXPECTED_ROUTES: tuple[tuple[str, str], ...] = (
    # Health
    ("GET", "/health"),
    ("GET", "/health/live"),
    ("GET", "/health/ready"),
    # Goal
    ("POST", "/api/v1/goals"),
    ("GET", "/api/v1/goals/{goal_id}"),
    ("GET", "/api/v1/goals"),
    ("PATCH", "/api/v1/goals/{goal_id}"),
    ("POST", "/api/v1/goals/{goal_id}/complete"),
    ("POST", "/api/v1/goals/{goal_id}/cancel"),
    # Nutrition
    ("POST", "/api/v1/nutrition"),
    ("GET", "/api/v1/nutrition/{nutrition_id}"),
    ("GET", "/api/v1/nutrition"),
    ("PATCH", "/api/v1/nutrition/{nutrition_id}"),
    ("PUT", "/api/v1/nutrition/{nutrition_id}/water"),
    ("PUT", "/api/v1/nutrition/{nutrition_id}/notes"),
    ("DELETE", "/api/v1/nutrition/{nutrition_id}"),
    # Progress
    ("POST", "/api/v1/progress"),
    ("GET", "/api/v1/progress/{progress_id}"),
    ("GET", "/api/v1/progress"),
    ("PUT", "/api/v1/progress/{progress_id}/body-composition"),
    ("PUT", "/api/v1/progress/{progress_id}/measurements"),
    ("PUT", "/api/v1/progress/{progress_id}/notes"),
    ("DELETE", "/api/v1/progress/{progress_id}"),
    # Readiness
    ("POST", "/api/v1/readiness"),
    ("GET", "/api/v1/readiness/{readiness_id}"),
    ("GET", "/api/v1/readiness"),
    ("PUT", "/api/v1/readiness/{readiness_id}/sleep"),
    ("PUT", "/api/v1/readiness/{readiness_id}/recovery-metrics"),
    ("PUT", "/api/v1/readiness/{readiness_id}/notes"),
    ("DELETE", "/api/v1/readiness/{readiness_id}"),
    # Workout + WorkoutSession
    ("POST", "/api/v1/workouts"),
    ("GET", "/api/v1/workouts/{workout_id}"),
    ("GET", "/api/v1/workouts"),
    ("PATCH", "/api/v1/workouts/{workout_id}"),
    ("POST", "/api/v1/workouts/{workout_id}/cancel"),
    ("POST", "/api/v1/workouts/{workout_id}/sessions"),
    ("GET", "/api/v1/workout-sessions/{session_id}"),
    ("POST", "/api/v1/workout-sessions/{session_id}/complete"),
    ("POST", "/api/v1/workout-sessions/{session_id}/sets"),
    ("POST", "/api/v1/workout-sessions/{session_id}/sets/complete"),
)


# FastAPI's own built-in routes (interactive docs UI, the raw OpenAPI
# JSON document itself) — real, correctly-registered routes, just not
# ones this phase implemented, so they're excluded from both directions
# of the comparison below rather than added to `_EXPECTED_ROUTES` (which
# exists to describe this phase's own 40 endpoints, not FastAPI's).
_FASTAPI_BUILTIN_ROUTES = {
    ("GET", "/docs"),
    ("GET", "/docs/oauth2-redirect"),
    ("GET", "/redoc"),
    ("GET", "/openapi.json"),
}


def _registered_routes(app: FastAPI) -> set[tuple[str, str]]:
    routes = set()
    for route in app.routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)
        if methods is None or path is None:
            continue  # pragma: no cover — only APIRoute has both; skip mounts/websockets
        for method in methods:
            if method != "HEAD":  # FastAPI auto-adds HEAD next to every GET
                routes.add((method, path))
    return routes - _FASTAPI_BUILTIN_ROUTES


@pytest.mark.unit
def test_every_expected_route_is_registered(live_app: FastAPI) -> None:
    registered = _registered_routes(live_app)
    missing = set(_EXPECTED_ROUTES) - registered
    assert not missing, f"routes never registered: {sorted(missing)}"


@pytest.mark.unit
def test_no_unexpected_routes_are_registered(live_app: FastAPI) -> None:
    """The inverse check — proves `_EXPECTED_ROUTES` above is a
    complete list, not just a subset, catching an accidental extra
    route as reliably as a missing one."""
    registered = _registered_routes(live_app)
    extra = registered - set(_EXPECTED_ROUTES)
    assert not extra, f"unexpected routes registered: {sorted(extra)}"


@pytest.mark.unit
def test_expected_route_count_matches_the_phase_task_list() -> None:
    """37 Application-Handler-backed endpoints (Workout 10, Nutrition 7,
    Progress 7, Readiness 7, Goal 6) plus 3 health endpoints — the exact
    count this phase's own task list specifies."""
    health_routes = [route for route in _EXPECTED_ROUTES if route[1].startswith("/health")]
    api_routes = [route for route in _EXPECTED_ROUTES if route[1].startswith("/api/v1")]
    assert len(health_routes) == 3
    assert len(api_routes) == 37


@pytest.mark.unit
def test_openapi_schema_generates_without_error(live_app: FastAPI) -> None:
    schema = live_app.openapi()

    assert schema["info"]["title"] == "Gym Companion API"
    assert schema["info"]["version"] == "0.1.0"
    assert "/api/v1/goals" in schema["paths"]


@pytest.mark.unit
def test_openapi_schema_paths_cover_every_expected_route(live_app: FastAPI) -> None:
    schema = live_app.openapi()
    schema_routes = {
        (method.upper(), path)
        for path, operations in schema["paths"].items()
        for method in operations
        if method != "head"
    }
    missing = set(_EXPECTED_ROUTES) - schema_routes
    assert not missing, f"routes missing from the generated OpenAPI schema: {sorted(missing)}"
