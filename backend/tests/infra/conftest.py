"""Fixtures for tests that need a real Postgres connection.

These tests are marked `integration` (registered in pyproject.toml, Step 5)
and skip themselves with a clear reason when no reachable database is
configured, rather than failing — a developer without Postgres running
locally should see "skipped: no database" for these, not a wall of
connection-refused errors, while `make backend-test`'s default run still
covers everything that doesn't need one.
"""

import os
from collections.abc import Generator

import pytest
import sqlalchemy
from alembic.config import Config
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from alembic import command
from app.core.config import get_settings
from app.infra.database import build_engine

TEST_DATABASE_URL = os.environ.get(
    "GYMTEST_DATABASE_URL",
    "postgresql+psycopg://gymcompanion:gymcompanion@localhost:5432/gymcompanion",
)


@pytest.fixture
def pg_session() -> Generator[Session, None, None]:
    engine = build_engine(TEST_DATABASE_URL)
    try:
        with engine.connect():
            pass
    except sqlalchemy.exc.OperationalError as exc:
        pytest.skip(f"no reachable Postgres at {TEST_DATABASE_URL}: {exc}")

    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def migrated_engine() -> Generator[Engine, None, None]:
    """Runs `alembic upgrade head` against TEST_DATABASE_URL, yields an
    engine bound to it, then runs `alembic downgrade base` — every test
    using this fixture starts and ends with a clean, unmigrated database,
    regardless of what the test itself does to the schema in between.

    Shared by `test_migrations.py` (schema-shape assertions) and
    `tests/infra/repositories/` (repository round-trip assertions against
    the real, migrated schema) — moved here from `test_migrations.py`,
    where it originated, once a second consumer needed the identical setup.

    Alembic's env.py reads the database URL from GYM_DATABASE_URL (via
    Settings), so pointing it at the test database is a matter of setting
    that environment variable for the duration of the fixture, exactly as
    a developer would from the command line — not a special test-only code
    path.
    """
    engine = build_engine(TEST_DATABASE_URL)
    try:
        with engine.connect():
            pass
    except sqlalchemy.exc.OperationalError as exc:
        pytest.skip(f"no reachable Postgres at {TEST_DATABASE_URL}: {exc}")

    original_url = os.environ.get("GYM_DATABASE_URL")
    os.environ["GYM_DATABASE_URL"] = TEST_DATABASE_URL
    get_settings.cache_clear()
    cfg = Config("alembic.ini")
    try:
        command.upgrade(cfg, "head")
        yield engine
    finally:
        command.downgrade(cfg, "base")
        if original_url is None:
            os.environ.pop("GYM_DATABASE_URL", None)
        else:
            os.environ["GYM_DATABASE_URL"] = original_url
        get_settings.cache_clear()
        engine.dispose()


@pytest.fixture
def session_factory(migrated_engine: Engine) -> sessionmaker[Session]:
    """A `sessionmaker` bound to the freshly migrated test database —
    what every `tests/infra/repositories/` test uses to open its own
    `Session` per repository call, the same "one session per unit of
    work" shape `test_migrations.py`'s own cross-tenant test already
    established (`with session_factory() as session, tenant_scope(...):
    ...`)."""
    return sessionmaker(bind=migrated_engine)
