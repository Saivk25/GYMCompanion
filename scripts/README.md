# Scripts

One-off developer scripts.

- `local_postgres.sh` — start/stop a local Postgres for backend development without
  Docker. See `backend/README.md`'s Postgres section for usage.
- `check_destructive_migrations.py` — static check (no database needed) that fails if a
  migration's `upgrade()` contains a destructive operation without an explicit review
  marker. Runs in CI (`.github/workflows/ci.yml`) and via `make
  backend-check-destructive-migrations`; see the script's own docstring for the exact
  rule and how to acknowledge an intentional destructive migration.

Database seeding (the exercise graph's initial curated set) is populated starting
Sprint 3 of the Engineering Master Plan.
