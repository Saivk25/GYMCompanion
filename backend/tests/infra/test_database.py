"""Tests for app/infra/database.py."""

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.infra.database import build_engine, tenant_scope


@pytest.mark.unit
def test_build_engine_is_lazy_and_does_not_connect() -> None:
    """SQLAlchemy engines are lazy: constructing one against an unreachable
    host must not raise, because no connection is opened until first use."""
    engine = build_engine("postgresql+psycopg://nobody:nowhere@localhost:1/nonexistent")

    assert isinstance(engine, Engine)


@pytest.mark.integration
def test_tenant_scope_sets_session_variable_for_the_transaction(
    pg_session: Session,
) -> None:
    with tenant_scope(pg_session, "11111111-1111-1111-1111-111111111111"):
        value = pg_session.execute(text("SELECT current_setting('app.current_user_id')")).scalar()

    assert value == "11111111-1111-1111-1111-111111111111"


@pytest.mark.integration
def test_tenant_scope_does_not_leak_across_transactions(pg_session: Session) -> None:
    with tenant_scope(pg_session, "22222222-2222-2222-2222-222222222222"):
        pass
    pg_session.commit()

    # SET LOCAL is scoped to the transaction that has ended above; a fresh
    # transaction must not still see it.
    value = pg_session.execute(text("SELECT current_setting('app.current_user_id', true)")).scalar()

    assert value in (None, "")
