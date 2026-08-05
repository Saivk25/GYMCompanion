"""Shared fixtures for API Layer tests.

Two distinct testing strategies live side by side in this package,
matching two distinct things worth proving about a thin HTTP layer:

1. **Routing/mapping tests** (`stub_client`, the overwhelming majority
   of this package) prove "does this route convert an `ApplicationResult`
   into the right HTTP status and body" — the only thing a route
   function itself does (see `app/api/routes/v1/goal.py`'s own module
   docstring). These override `app.api.deps.get_container` with
   `_StubContainer`, a fake that resolves any handler type to a
   `_StubHandler` wrapping one fixed `ApplicationResult` — no real
   handler, no real database, no real `UnitOfWork` in the loop, on
   purpose: a handler's own business logic is `tests/application/`'s
   job, not this package's. Since the override replaces `get_container`
   before any route ever reads `request.app.state.container`, these
   clients never need FastAPI's lifespan to run at all. `get_current_user_id`
   is separately overridden to always return one fixed `UserId` (`_A_USER_ID`
   below) — proving "does this route require authentication" is
   `app/api/deps.py`'s own dependency's job (see `tests/api/test_deps.py`),
   not something every route test needs to re-prove by attaching a real
   bearer token to every single request.

2. **Live-lifespan tests** (`live_client`) prove the small number of
   things that only exist once `app.composition.bootstrap.bootstrap()`
   has actually run — `/health/ready`'s real connectivity check,
   OpenAPI generation against the fully-wired app. These point
   `GYM_DATABASE_URL` at sqlite (a real, always-reachable connection —
   see `tests/composition/test_bootstrap.py`'s identical reasoning for
   why sqlite is sufficient here without needing a real Postgres).

3. **Full-stack integration tests** (`live_migrated_client`, used only by
   `tests/api/test_auth_flow_integration.py`) run the real `register` ->
   `login` -> `refresh` -> `logout` -> `me` flow, and a real protected
   `v1` route, against an actually-migrated Postgres database — the one
   place in this package a request travels all the way through
   `RegisterHandler`/`LoginHandler`/etc. into `bcrypt`/PyJWT/SQLAlchemy
   and back, rather than a stub. Reuses `tests/infra/conftest.py`'s own
   `TEST_DATABASE_URL` and `alembic upgrade head`/`downgrade base`
   pattern (see that module's docstring) — same "skip with a clear
   reason, don't fail, when no Postgres is reachable" convention every
   other integration test in this codebase already follows.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from typing import Any

import pytest
import sqlalchemy
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient

from alembic import command
from app.api.deps import get_container, get_current_user_id
from app.application.shared.application_result import ApplicationResult
from app.core.config import get_settings
from app.domain.user.identifiers import UserId
from app.infra.database import build_engine
from app.main import create_app
from tests.infra.conftest import TEST_DATABASE_URL

_A_USER_ID = UserId.generate()


class _StubHandler:
    """Stands in for a real Application Layer handler — `handle()`
    always returns the one `ApplicationResult` it was constructed with,
    regardless of the request it's asked to handle."""

    def __init__(self, result: ApplicationResult[Any]) -> None:
        self._result = result

    def handle(self, request: object) -> ApplicationResult[Any]:
        del request
        return self._result


class _StubContainer:
    """Stands in for `app.composition.container.Container` — resolves
    every handler type to the same `_StubHandler`. Duck-typed against
    `Container`'s own `handler()` signature (the only method any route
    actually calls through `handler_dependency`); it does not subclass
    `Container` since FastAPI's dependency override mechanism has no
    need for it to."""

    def __init__(self, result: ApplicationResult[Any]) -> None:
        self._result = result

    def handler(self, handler_type: type) -> _StubHandler:
        del handler_type
        return _StubHandler(self._result)


@pytest.fixture
def stub_client() -> Callable[[ApplicationResult[Any]], TestClient]:
    """Returns a factory: given an `ApplicationResult`, returns a
    `TestClient` whose every route resolves to a handler that always
    returns that exact result. See the module docstring."""

    def _make(result: ApplicationResult[Any]) -> TestClient:
        app = create_app()
        app.dependency_overrides[get_container] = lambda: _StubContainer(result)
        app.dependency_overrides[get_current_user_id] = lambda: _A_USER_ID
        # raise_server_exceptions=False: Starlette's ServerErrorMiddleware
        # always re-raises an unhandled exception after sending its response
        # ("We always continue to raise the exception... allows test clients
        # to optionally raise the error within the test case" — its own
        # source comment) regardless of whether a custom handler produced
        # that response. This API's job is precisely to turn such an
        # exception into a structured HTTP response (see `app/api/errors.
        # py`'s `_unhandled_exception_handler`) — a test of that behavior
        # needs the response TestClient already received, not a re-raised
        # Python exception standing in for it.
        return TestClient(app, raise_server_exceptions=False)

    return _make


@pytest.fixture
def authenticated_user_id() -> UserId:
    """The exact `UserId` `stub_client` overrides `get_current_user_id`
    to return — exposed so a test that needs to assert *which* caller a
    route acted as (rather than just that the call succeeded) doesn't
    need to reach into `conftest.py`'s own private `_A_USER_ID`."""
    return _A_USER_ID


@pytest.fixture
def live_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """A `TestClient` whose lifespan actually runs `bootstrap()` against
    sqlite. See the module docstring."""
    monkeypatch.setenv("GYM_DATABASE_URL", "sqlite://")
    monkeypatch.setenv("GYM_ENVIRONMENT", "test")
    get_settings.cache_clear()
    try:
        with TestClient(create_app(), raise_server_exceptions=False) as client:
            yield client
    finally:
        get_settings.cache_clear()


@pytest.fixture
def live_migrated_client() -> Iterator[TestClient]:
    """A `TestClient` running the fully-wired app against a real,
    freshly `alembic upgrade head`-ed Postgres database — skips with a
    clear reason if `TEST_DATABASE_URL` (`tests/infra/conftest.py`)
    isn't reachable, the same convention every other integration test
    in this codebase follows. Downgrades back to `base` on teardown, so
    a run of this fixture never leaves state for the next one.
    """
    engine = build_engine(TEST_DATABASE_URL)
    try:
        with engine.connect():
            pass
    except sqlalchemy.exc.OperationalError as exc:
        pytest.skip(f"no reachable Postgres at {TEST_DATABASE_URL}: {exc}")
    finally:
        engine.dispose()

    original_url = os.environ.get("GYM_DATABASE_URL")
    os.environ["GYM_DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["GYM_ENVIRONMENT"] = "test"
    get_settings.cache_clear()
    cfg = Config("alembic.ini")
    try:
        command.upgrade(cfg, "head")
        with TestClient(create_app(), raise_server_exceptions=False) as client:
            yield client
    finally:
        command.downgrade(cfg, "base")
        if original_url is None:
            os.environ.pop("GYM_DATABASE_URL", None)
        else:
            os.environ["GYM_DATABASE_URL"] = original_url
        get_settings.cache_clear()


@pytest.fixture
def live_app(monkeypatch: pytest.MonkeyPatch) -> Iterator[FastAPI]:
    """The underlying `FastAPI` app for tests that need to inspect it
    directly (e.g. OpenAPI schema generation) rather than issue HTTP
    requests through a `TestClient`."""
    monkeypatch.setenv("GYM_DATABASE_URL", "sqlite://")
    monkeypatch.setenv("GYM_ENVIRONMENT", "test")
    get_settings.cache_clear()
    try:
        yield create_app()
    finally:
        get_settings.cache_clear()
