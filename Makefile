# Gym Companion — developer entry points.
#
# This exists so "how do I run the tests" never requires remembering flags or
# which directory to be in. Every target is a thin wrapper; the actual
# configuration lives in backend/pyproject.toml and apps/mobile/pubspec.yaml.
#
# Backend targets assume a virtual environment has been created (see
# backend/README.md) — point VENV at it, e.g.:
#   make backend-test VENV=~/.venvs/gym-backend
#
# Note: backend-install intentionally does NOT use `pip install -e`. A plain
# (non-editable) install of the backend[dev] extra is enough — the app is run
# via PYTHONPATH, not via the installed console entry point — and editable
# installs were found to hang in at least one development environment during
# Sprint 1 (see docs/adr/0002-flutter-verification-constraint.md's sibling
# note in the Step 4 commit message for the equivalent backend finding).
VENV ?= .venv
PY := $(abspath $(VENV))/bin/python

.PHONY: backend-install backend-test backend-lint backend-format backend-typecheck backend-run \
        backend-migrate backend-migrate-down backend-migration backend-migrate-check \
        mobile-get mobile-analyze mobile-test mobile-run \
        precommit-install check

backend-install:
	$(PY) -m pip install "./backend[dev]"

backend-test:
	cd backend && PYTHONPATH=. $(PY) -m pytest

backend-lint:
	cd backend && $(PY) -m ruff check .

backend-format:
	cd backend && $(PY) -m ruff format .

backend-typecheck:
	cd backend && PYTHONPATH=. $(PY) -m mypy app tests

backend-run:
	cd backend && PYTHONPATH=. $(PY) -m uvicorn app.main:app --reload

# Applies every migration up to the latest. Reads the target database from
# GYM_DATABASE_URL (see backend/.env.example) — same variable the app itself
# uses, so there is never a question of which database a migration ran
# against.
backend-migrate:
	cd backend && PYTHONPATH=. $(PY) -m alembic upgrade head

# Reverts exactly one migration. Named "-down" rather than mirroring
# "migrate" 1:1 because rollback is a deliberately rarer, more dangerous
# action than moving forward — it should not be one keystroke away from
# backend-migrate.
backend-migrate-down:
	cd backend && PYTHONPATH=. $(PY) -m alembic downgrade -1

# Generates a new migration from the current app/infra/models.py against
# the database's current schema. Requires a message: `make backend-migration
# m="add profile table"`. Always read the generated file before committing —
# autogenerate detects table/column/constraint changes but knows nothing
# about RLS policies, which must still be added by hand (see the Step 10
# migration for the pattern).
backend-migration:
	cd backend && PYTHONPATH=. $(PY) -m alembic revision --autogenerate -m "$(m)"

# Fails if app/infra/models.py and the latest migration have drifted apart
# — i.e. someone changed a model and forgot to generate a migration for it.
# Cheap enough to run in CI (Step 11) on every push.
backend-migrate-check:
	cd backend && PYTHONPATH=. $(PY) -m alembic check

mobile-get:
	cd apps/mobile && flutter pub get

mobile-analyze:
	cd apps/mobile && flutter analyze

mobile-test:
	cd apps/mobile && flutter test

mobile-run:
	cd apps/mobile && flutter run

precommit-install:
	$(PY) -m pre_commit install

# Everything CI runs on the backend, in one command, before you push.
# backend-migrate-check is deliberately excluded: it needs a real database,
# and this target must stay runnable offline (e.g. before Postgres is
# started locally). CI runs it separately, against a service container.
check: backend-lint backend-typecheck backend-test
