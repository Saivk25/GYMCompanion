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
from sqlalchemy.orm import Session, sessionmaker

from app.infra.database import build_engine

_TEST_DATABASE_URL = os.environ.get(
    "GYM_TEST_DATABASE_URL",
    "postgresql+psycopg://gymcompanion:gymcompanion@localhost:5432/gymcompanion",
)


@pytest.fixture
def pg_session() -> Generator[Session, None, None]:
    engine = build_engine(_TEST_DATABASE_URL)
    try:
        with engine.connect():
            pass
    except sqlalchemy.exc.OperationalError as exc:
        pytest.skip(f"no reachable Postgres at {_TEST_DATABASE_URL}: {exc}")

    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
