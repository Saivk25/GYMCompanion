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

Copy `.env.example` to `.env` and adjust `GYM_DATABASE_URL` once Postgres is available
(Sprint 1, Step 9).

Run the API:

```bash
uvicorn app.main:app --reload
```

Run the tests:

```bash
pytest
```

## Status

Sprint 1, Step 2 (this scaffold): a booting FastAPI app with a `/health` endpoint and one
passing test, nothing product-specific yet. Domain Core lands in Step 12.
