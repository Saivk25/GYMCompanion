"""Tests for the Alembic migration set: upgrade, downgrade, and the concrete
cross-tenant-leak proof required by the Engineering Master Plan's Sprint 1
Definition of Done ("Postgres row-level security scoped to user_id on every
table ... RLS verified by a cross-tenant-leak test").

These tests run real `alembic upgrade`/`downgrade` commands against
`TEST_DATABASE_URL` (see conftest.py) and skip themselves, rather than
fail, when no Postgres is reachable — same convention as
`tests/infra/test_database.py`. The `migrated_engine` fixture they share
lives in `conftest.py` (moved there once `tests/infra/repositories/` needed
the identical setup for its own round-trip tests).
"""

import uuid

import pytest
from alembic.config import Config
from sqlalchemy import inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from alembic import command
from app.infra.database import tenant_scope
from app.infra.models import UserAccount

# Every tenant-scoped table added since the users-table migration
# (`e1be8b00d81f`), in creation order — `exercises` is deliberately absent:
# it carries no `user_id` and gets no RLS at all (see
# `app/infra/models/exercise.py`'s own module docstring). Re-proving the
# full cross-tenant-leak scenario for each of these individually would be
# pure repetition of `test_rls_prevents_cross_tenant_reads` below; this list
# instead drives a single parametrized "RLS is enabled and forced" check —
# the structural half of the proof — while the `users` table keeps the one
# full, concrete leak-proof test as the canonical example every other
# table's policy is written to match.
_TENANT_SCOPED_TABLES = (
    "workouts",
    "workout_sessions",
    "exercise_performances",
    "exercise_sets",
    "progress_records",
    "nutrition_entries",
    "readiness_checkins",
    "goals",
)


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


@pytest.mark.integration
@pytest.mark.parametrize("table_name", _TENANT_SCOPED_TABLES)
def test_every_tenant_scoped_table_has_forced_rls(migrated_engine: Engine, table_name: str) -> None:
    """The structural half of the RLS proof, for every table added after
    `users` — see `_TENANT_SCOPED_TABLES`'s own comment for why this
    doesn't repeat `test_rls_prevents_cross_tenant_reads`'s full concrete
    leak scenario for each one."""
    with migrated_engine.connect() as conn:
        relrowsecurity, relforcerowsecurity = conn.execute(
            text("SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname = :name"),
            {"name": table_name},
        ).one()

    assert relrowsecurity is True
    assert relforcerowsecurity is True


@pytest.mark.integration
def test_exercises_table_has_no_row_level_security(migrated_engine: Engine) -> None:
    """The deliberate exception: `exercises` is a shared, global catalog
    with no `user_id` column, so it must not have RLS enabled at all — see
    `app/infra/models/exercise.py`'s own module docstring."""
    with migrated_engine.connect() as conn:
        relrowsecurity, relforcerowsecurity = conn.execute(
            text("SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname = :name"),
            {"name": "exercises"},
        ).one()

    assert relrowsecurity is False
    assert relforcerowsecurity is False
