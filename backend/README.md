# Gym Companion — backend

FastAPI service over a framework-free domain core. See `docs/Gym_Companion_Engineering_Master_Plan.docx`
(repository root) for the full rationale; this file only covers running the code.

## Layout

- `app/domain/` — framework-free business logic (entities, state machines, rule engines).
  Depends on nothing outside the Python standard library — not `api/`, not `infra/`, not
  even `pydantic` — enforced by a static test, not just convention (see "Domain Core"
  below). `app/domain/shared_kernel/` is the base-type toolkit every future aggregate
  builds on (Sprint 2 onward); no per-aggregate business logic exists yet.
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

## Domain Core

`app/domain/shared_kernel/` is the framework-independent foundation every real aggregate
(Sprint 2 onward) is built from — not business logic itself, but the base types that make
writing it consistent:

| Module | Provides |
|---|---|
| `identifiers.py` | `EntityId` — subclass per aggregate (`class UserId(EntityId)`) for compile-time-checked, non-interchangeable ids. |
| `clock.py` | `Clock` / `SystemClock` / `FixedClock` — time as an injected dependency, never a bare `datetime.now()` call. |
| `value_object.py` | `ValueObject` — immutable, equality-by-value base; frozen-dataclass inheritance makes forgetting `frozen=True` a `TypeError` at import time, not a runtime bug. |
| `entity.py` | `Entity` — identity-based (not field-based) equality and hashing. |
| `aggregate_root.py` | `AggregateRoot` — adds the domain-event recording/draining lifecycle on top of `Entity`. |
| `events.py` | `DomainEvent` — immutable, `occurred_at`-stamped record of something that already happened. |
| `errors.py` | `DomainError` (an expected, returnable failure) vs. `DomainInvariantViolationError` (a raised bug) — see the module docstring for the distinction. |
| `result.py` | `Ok[T]` / `Err[E]` — expected failures as values instead of exceptions. |
| `repository.py` | `Repository[TAggregate, TId]` — the persistence contract `app/infra/` implements; domain code depends on this interface, never on SQLAlchemy. |
| `service.py` | `DomainService` — marker base for stateless cross-aggregate logic (the nine rule engines, starting Sprint 2+). |
| `validation.py` | `ensure()` / `ensure_not_empty()` / `ensure_positive()` — guard clauses that raise `DomainInvariantViolationError`. |

Every name is re-exported from `app.domain.shared_kernel` directly, so real aggregate
code writes one import instead of several — see that package's `__init__.py`.

### The one architecture rule, enforced statically

"Domain depends on nothing but the Python standard library" is not just documented — it's
a real test. `tests/domain/test_import_boundaries.py` parses every file under
`app/domain/` with `ast` and checks every import's target against
`sys.stdlib_module_names` (a positive allow-list, so a *new* forbidden dependency is
caught automatically, not just the ones anyone thought to ban). This runs as part of the
normal test suite and again as CI's own dedicated gate — see below.

```bash
make backend-test-domain-coverage   # import-boundary test + 100%-coverage gate, domain only
```

`app/domain` carries its own, stricter, 100%-coverage requirement, separate from the rest
of the backend (`pyproject.toml`'s `[tool.coverage.report]` explains why it can't just be
one repo-wide number) — matching the Engineering Master Plan's testing strategy table:
"Domain Core ... near-100% coverage ... merge-blocking."

## Continuous integration

`.github/workflows/ci.yml` runs on every push and pull request: lint, format check,
mypy strict, migration verification and drift detection, the destructive-migration
content check (`scripts/check_destructive_migrations.py`), the Domain Core import-boundary
and 100%-coverage gate, the full pytest suite against a real Postgres service container, a
Docker image build with an import smoke test, and Flutter analyze/test. See the workflow
file itself for why it's structured as independent parallel jobs rather than one long
sequential one, and why there's no Python-version/OS matrix.

## Status

Sprint 1, Step 12: the Domain Core skeleton (`app/domain/shared_kernel/`) is in place —
base types only, no product-specific business logic yet (see "Domain Core" above). Every
one of Sprint 1's twelve steps is now done. Real aggregates, the nine rule engines, and
everything product-specific start with Sprint 2.
