"""Tests for the Alembic migration set: upgrade, downgrade, and the concrete
cross-tenant-leak proof required by the Engineering Master Plan's Sprint 1
Definition of Done ("Postgres row-level security scoped to user_id on every
table ... RLS verified by a cross-tenant-leak test").

These tests run real `alembic upgrade`/`downgrade` commands against
`TEST_DATABASE_URL` (see conftest.py) and skip themselves, rather than
fail, when no Postgres is reachable — same convention as
`tests/infra/test_database.py`.
"""

import os
import uuid
from collections.abc import Generator

import pytest
import sqlalchemy
from alembic.config import Config
from sqlalchemy import inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from alembic import command
from app.core.config import get_settings
from app.infra.database import build_engine, tenant_scope
from app.infra.models import UserAccount
from tests.infra.conftest import TEST_DATABASE_URL


@pytest.fixture
def migrated_engine() -> Generator[Engine, None, None]:
    """Runs `alembic upgrade head` against TEST_DATABASE_URL, yields an
    engine bound to it, then runs `alembic downgrade base` — every test
    using this fixture starts and ends with a clean, unmigrated database,
    regardless of what the test itself does to the schema in between.

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


@pytest.mark.integration
def test_upgrade_creates_users_table_with_forced_rls(migrated_engine: Engine) -> None:
    inspector = inspect(migrated_engine)
    assert "users" in inspector.get_table_names()

    with migrated_engine.connect() as conn:
        relrowsecurity, relforcerowsecurity = conn.execute(
            text("SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname = 'users'")
        ).one()

    # Both must be true: relrowsecurity enables RLS at all; relforcerowsecurity
    # is what makes it apply to the table owner (the role this app connects
    # as) rather than being silently bypassed. See the migration's docstring.
    assert relrowsecurity is True
    assert relforcerowsecurity is True


@pytest.mark.integration
def test_downgrade_removes_table_and_reupgrade_recreates_it(migrated_engine: Engine) -> None:
    """Proves rollback actually works, not just that a downgrade() function
    exists — downgrades mid-test, confirms the table is gone, then
    re-upgrades and confirms it's back, all against the real database."""
    cfg = Config("alembic.ini")

    command.downgrade(cfg, "base")
    assert "users" not in inspect(migrated_engine).get_table_names()

    command.upgrade(cfg, "head")
    assert "users" in inspect(migrated_engine).get_table_names()


@pytest.mark.integration
def test_rls_prevents_cross_tenant_reads(migrated_engine: Engine) -> None:
    """The cross-tenant-leak test itself.

    Two users are inserted under two different tenant scopes. A session
    scoped to user A must see exactly user A's row — never user B's, and
    nothing at all if no tenant scope is set. This is what actually proves
    the RLS policy (not just its SQL text) does what the Architecture
    document requires.

    Follows the pattern documented on UserAccount and in the creating
    migration: the id is generated in Python and the tenant scope is set
    *before* the row is inserted, because the ORM's insert also reads the
    row back to populate server-default columns, and that read-back is
    itself governed by RLS.
    """
    session_factory = sessionmaker(bind=migrated_engine)
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    for user_id, locale in ((user_a_id, "en-US"), (user_b_id, "en-GB")):
        with session_factory() as session, tenant_scope(session, str(user_id)):
            session.add(
                UserAccount(
                    user_id=user_id,
                    locale=locale,
                    timezone="UTC",
                    auth_method="password",
                )
            )
            session.commit()

    with session_factory() as session, tenant_scope(session, str(user_a_id)):
        visible_to_a = session.scalars(select(UserAccount)).all()
    assert [row.user_id for row in visible_to_a] == [user_a_id]

    with session_factory() as session, tenant_scope(session, str(user_b_id)):
        visible_to_b = session.scalars(select(UserAccount)).all()
    assert [row.user_id for row in visible_to_b] == [user_b_id]

    with session_factory() as session:
        # No tenant scope set at all: RLS must default-deny, not
        # default-allow. FORCE ROW LEVEL SECURITY plus a USING clause with
        # no matching current_setting is what makes this an empty result
        # instead of every row in the table.
        visible_to_nobody = session.scalars(select(UserAccount)).all()
    assert visible_to_nobody == []
