"""Database engine, session factory, and the row-level-security convention.

This module is the only place in the codebase that knows how to open a
connection to Postgres. Everything else — repositories, API dependencies —
gets a Session from here.

Row-level security (RLS): every per-user table (added starting with the first
real migration, Sprint 1 Step 10) has a policy that filters rows against the
Postgres session variable `app.current_user_id`. `tenant_scope` below is the
single place that sets it, scoped to the current transaction (via
`set_config(..., is_local=true)`) so it never leaks across connections in a
pool. No query anywhere in this codebase is allowed to filter by user_id in
application code as a substitute for this — that would be the exact mistake
the Architecture document's Section 19 (item 1) and this project's
multi-tenant-from-day-one decision exists to prevent.
"""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def build_engine(database_url: str | None = None) -> Engine:
    """Create a SQLAlchemy engine.

    Accepts an explicit URL (used by tests to point at a throwaway database)
    rather than always reading global settings, so engine construction stays
    testable without monkeypatching.
    """
    url = database_url or get_settings().database_url
    return create_engine(url, pool_pre_ping=True)


_engine: Engine = build_engine()
SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a Session, always closed after the request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def tenant_scope(session: Session, user_id: str) -> Generator[Session, None, None]:
    """Scope every query inside this block to a single tenant via RLS.

    Uses `set_config('app.current_user_id', ..., true)` rather than
    `SET LOCAL app.current_user_id = ...` because Postgres does not accept
    bind parameters for `SET`/`SET LOCAL` over the extended query protocol
    (it raises a syntax error) — `set_config` is a regular function, so
    parameter binding works normally and this stays injection-safe.
    `is_local=true` is what ties the setting to the current transaction, so
    it is reset automatically on commit/rollback, and there is no way for
    one request's tenant scope to bleed into the next request on a pooled
    connection.
    """
    session.execute(
        text("SELECT set_config('app.current_user_id', :user_id, true)"),
        {"user_id": user_id},
    )
    yield session
