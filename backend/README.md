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
  see its docstring before writing any query that touches per-user data.
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

## Status

Sprint 1, Step 9: `app/infra/database.py` (engine, session factory, RLS `tenant_scope`
convention) exists and is verified against a real local Postgres instance, including a
test proving the tenant scope does not leak across transactions. No SQLAlchemy models or
migrations yet — those land in Step 10 (Alembic) and Step 12 (Domain Core). A booting
FastAPI app with a `/health` endpoint, nothing product-specific yet.
