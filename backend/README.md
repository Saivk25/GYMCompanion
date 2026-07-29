# Gym Companion — backend

FastAPI service over a framework-free domain core. See `docs/Gym_Companion_Engineering_Master_Plan.docx`
(repository root) for the full rationale; this file only covers running the code.

## Layout

- `app/domain/` — framework-free business logic (entities, state machines, rule engines).
  Imports nothing from `api/` or `infra/`. Populated starting Sprint 1, Step 12.
- `app/api/` — thin FastAPI routers and Pydantic schemas over `app/domain/`.
- `app/ai/` — the AI Adapter Layer (vendor-agnostic vision/language provider interfaces).
  Empty until Sprint 1 (Alpha milestone) per the Engineering Master Plan.
- `app/infra/` — SQLAlchemy models, repositories, the only place that knows about Postgres.
  `database.py` owns the engine/session and the row-level-security convention (`tenant_scope`);
  see its docstring before writing any query that touches per-user data. `models.py` holds
  the ORM mapping classes (persistence shape only — not the Domain Core). `orm_base.py`
  holds the shared declarative base and naming convention Alembic autogenerate relies on.
- `app/jobs/` — background job definitions. Empty until real async job volume exists.
- `app/core/` — cross-cutting concerns (currently just configuration).
- `tests/` — mirrors `app/` 1:1. `tests/domain/` never touches a database.

## Local development

This project's dependencies are declared in `pyproject.toml`. Create a virtual environment
**outside this repository** if your editor/tooling struggles with an in-tree `.venv` on a
synced/mounted drive:

```bash
python3 -m venv ~/.venvs/gym-backend
~/.venvs/gym-backend/bin/pip install -e ".[dev]"
```

(The `dev` extra — pytest, ruff, mypy, pre-commit — is added in Sprint 1, Step 4.)

For a reproducible install that matches exactly what CI ran — the exact, hash-pinned
dependency versions in `requirements-lock.txt`, rather than pyproject.toml's ranges
resolved fresh — use `make backend-install-locked` instead. See "Reproducible builds"
below.

Copy `.env.example` to `.env` and adjust `GYM_DATABASE_URL` once Postgres is available.

Run the API:

```bash
uvicorn app.main:app --reload
```

Run the tests:

```bash
pytest
```

## Postgres

Two ways to get a local Postgres for development, either works:

- **Docker Compose** (simplest if you have Docker): `cd infra && docker compose up` — see
  `infra/README.md`.
- **`scripts/local_postgres.sh`** (no Docker required, uses your system's installed Postgres):
  ```bash
  scripts/local_postgres.sh start
  ```
  This initializes a data directory under `~/.gym-companion/pgdata` on first run, and creates
  the `gymcompanion` role/database. It prints the connection URL to export as
  `GYM_DATABASE_URL` (for running the app) and `GYM_TEST_DATABASE_URL` (for running the
  integration tests below). Stop it with `scripts/local_postgres.sh stop`.

### Row-level security convention

Every per-tenant table is protected by a Postgres RLS policy keyed on the session variable
`app.current_user_id`. `app/infra/database.py`'s `tenant_scope()` context manager is the
**only** place in the codebase allowed to set it — application code must never filter
per-user tables by `user_id` in a `WHERE` clause as a substitute for RLS. This is a
"never do this" rule, not a style preference: see the Architecture document's Section 19
and `app/infra/database.py`'s docstring for why.

### Integration tests

`tests/infra/` contains tests that need a real Postgres connection
(`@pytest.mark.integration`). They read `GYM_TEST_DATABASE_URL` (falling back to the same
default as `GYM_DATABASE_URL`) and **skip themselves with a clear reason** — they do not
fail the suite — if no Postgres is reachable. Point `GYM_TEST_DATABASE_URL` at a throwaway
database, never at one with real data.

## Database migrations (Alembic)

```bash
make backend-migrate              # apply every migration up to head
make backend-migrate-down         # revert exactly one migration
make backend-migration m="add profile table"   # autogenerate a new migration
make backend-migrate-check        # fail if models.py and the latest migration have drifted
```

All four read the target database from `GYM_DATABASE_URL` — same variable, same `.env`,
as the running app. There is no separate migrations config to keep in sync.

Workflow for a schema change: edit `app/infra/models.py`, run `make backend-migration
m="..."`, **read the generated file** in `alembic/versions/` before committing it —
autogenerate detects table/column/constraint changes but knows nothing about row-level
security, which must be added by hand in the migration (see
`alembic/versions/..._create_users_table_with_row_level_.py` for the pattern: `ENABLE
ROW LEVEL SECURITY`, `FORCE ROW LEVEL SECURITY`, then `CREATE POLICY`), then run `make
backend-migrate` against a real database and confirm it applies cleanly before opening a
PR.

Naming: migration files are timestamp-prefixed (`alembic.ini`'s `file_template`) so
`alembic/versions/` sorts chronologically. Constraint/index names come from a fixed
naming convention (`app/infra/orm_base.py`) so autogenerated names are deterministic
rather than Postgres-assigned. Every autogenerated file is run through `ruff format` and
`ruff check --fix` automatically (`alembic.ini`'s `post_write_hooks`), so it never fails
`make check` on its own.

### A hard-won RLS + migrations lesson

Two things about `FORCE ROW LEVEL SECURITY` are not obvious and both were caught only by
testing against a real database, not by reading the code:

1. A policy with no explicit `WITH CHECK` reuses its `USING` expression for inserts too —
   which means the *first* row in a tenant-root table (an account signup) can never be
   inserted, since there's no tenant to check against yet. The `users` migration's policy
   has `WITH CHECK (true)` specifically to allow this.
2. `WITH CHECK (true)` only covers a bare `INSERT`. An `INSERT ... RETURNING` — the normal
   ORM pattern — also reads the new row back, and that read is governed by `USING`, not
   `WITH CHECK`. The correct application-level pattern (documented on `UserAccount` in
   `app/infra/models.py`) is to generate the new user's id in Python and call
   `tenant_scope(session, str(new_id))` *before* inserting, so the id already matches by
   the time Postgres evaluates `RETURNING`. `tests/infra/test_migrations.py`'s
   cross-tenant test exercises exactly this pattern.

## Reproducible builds

`requirements-lock.txt` pins every dependency (direct and transitive) to an exact,
hash-verified version. CI (`.github/workflows/ci.yml`) installs from this file, not from
`pyproject.toml`'s ranges — so a build today and a build in six months resolve to
identical versions, until someone deliberately regenerates the lock file:

```bash
make backend-lock                 # regenerate after changing a dependency
make backend-install-locked       # install exactly what's locked (what CI does)
```

Review the diff before committing a regenerated lock file — it's the only way a
dependency bump becomes visible in code review, since `pyproject.toml`'s own ranges
often don't change at all when only a transitive dependency moves.

## Continuous integration

`.github/workflows/ci.yml` runs on every push and pull request: lint, format check,
mypy strict, migration verification and drift detection, the destructive-migration
content check (`scripts/check_destructive_migrations.py`), the full pytest suite against
a real Postgres service container, a Docker image build with an import smoke test, and
Flutter analyze/test. See the workflow file itself for why it's structured as
independent parallel jobs rather than one long sequential one, and why there's no
Python-version/OS matrix.

## Status

Sprint 1, Step 11: CI is wired end to end (see above). All eleven of Sprint 1's steps
that don't depend on product code are done; the initial Domain Core skeleton (Step 12)
is what's left.
