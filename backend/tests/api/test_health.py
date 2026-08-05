"""Tests for the health/liveness/readiness endpoints
(`app/api/routes/health.py`)."""

import pytest
from fastapi.testclient import TestClient

from app.composition.container import Container


@pytest.mark.unit
def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.unit
def test_health_live_returns_ok(client: TestClient) -> None:
    """No lifespan needed — `/health/live` has no dependency on the
    database or the `Container`, the same as `/health` itself."""
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.unit
def test_health_ready_returns_ready_when_the_database_is_reachable(
    live_client: TestClient,
) -> None:
    """`live_client` (`tests/api/conftest.py`) runs the real lifespan
    against sqlite — a real, always-reachable connection — so this is a
    genuine end-to-end proof that `/health/ready` calls `Container.
    is_database_ready()` and gets `True` back."""
    response = live_client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.unit
def test_health_ready_returns_503_when_the_database_is_unreachable(
    live_client: TestClient,
) -> None:
    """Swaps the live app's real `Container` for one whose
    `is_database_ready()` always returns `False` — proving the 503
    mapping without needing an actually-broken database connection."""

    class _AlwaysUnreadyContainer:
        def is_database_ready(self) -> bool:
            return False

    live_client.app.state.container = _AlwaysUnreadyContainer()  # type: ignore[attr-defined]

    response = live_client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == "database unavailable"


@pytest.mark.unit
def test_health_ready_uses_the_real_container_type(live_client: TestClient) -> None:
    """A sanity check that `live_client`'s lifespan actually wired a
    real `Container`, not a stub — the negative-path test above proves
    the 503 branch works, this proves the positive-path test above was
    exercising the real thing, not an accidental no-op."""
    assert isinstance(live_client.app.state.container, Container)  # type: ignore[attr-defined]
