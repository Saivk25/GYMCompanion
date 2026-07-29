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

.PHONY: backend-install backend-install-locked backend-lock backend-test backend-lint \
        backend-format backend-typecheck backend-run backend-test-domain-coverage \
        backend-migrate backend-migrate-down backend-migration backend-migrate-check \
        backend-check-destructive-migrations \
        mobile-get mobile-analyze mobile-test mobile-run \
        precommit-install check

backend-install:
	$(PY) -m pip install "./backend[dev]"

# The reproducible counterpart to backend-install: installs the exact,
# hash-verified versions in backend/requirements-lock.txt instead of letting
# pip re-resolve pyproject.toml's ranges fresh. This is what CI uses (Step
# 11) so a build never silently picks up a new transitive dependency
# release between one run and the next. Local dev defaults to
# backend-install for faster iteration; reach for this when you specifically
# need to reproduce what CI saw.
backend-install-locked:
	$(PY) -m pip install -r backend/requirements-lock.txt
	$(PY) -m pip install --no-deps ./backend

# Regenerates backend/requirements-lock.txt from backend/pyproject.toml.
# Run this after changing a dependency, review the diff, then commit the
# lock file alongside the pyproject.toml change — the two must move
# together. Needs pip-tools, which is deliberately not a permanent project
# dependency (only needed for this one occasional task):
#   $(PY) -m pip install pip-tools
backend-lock:
	cd backend && $(PY) -m piptools compile --extra dev --generate-hashes \
		--output-file=requirements-lock.txt pyproject.toml

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

# app/domain's own, stricter coverage gate: 100%, merge-blocking, run
# separately from backend-test because coverage.py's fail_under in
# pyproject.toml is a single repo-wide number and app/infra/app/api
# legitimately aren't at 100% yet (see pyproject.toml's [tool.coverage.report]
# comment). Only tests/domain is in scope here — this is specifically about
# the Domain Core's own promise, not a proxy for overall backend health.
#
# Wrapped with the standalone `coverage` command (--source=app.domain) and
# pytest-cov disabled for this one run (--no-cov) rather than just adding
# --cov=app.domain on top of pytest-cov: pytest-cov *adds* --cov sources to
# whatever addopts already has (--cov=app), it does not replace them, which
# would silently measure and fail this gate against the whole app/ package
# instead of app/domain alone — found by actually running this target, not
# assumed to work.
backend-test-domain-coverage:
	cd backend && PYTHONPATH=. $(PY) -m coverage run --source=app.domain \
		-m pytest tests/domain --no-cov -q
	cd backend && $(PY) -m coverage report --fail-under=100 -m

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

# Static check (no database needed): fails if any migration's upgrade()
# contains a destructive operation (DROP TABLE/COLUMN, TRUNCATE) without an
# explicit review marker comment. Implements the Engineering Master Plan's
# CI/CD section: "no destructive migration runs without a prior backup
# step, enforced by a CI check on migration file content." See
# scripts/check_destructive_migrations.py for the exact rule and how to
# acknowledge an intentional destructive migration.
backend-check-destructive-migrations:
	$(PY) scripts/check_destructive_migrations.py

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

# Everything CI runs on the backend that doesn't need a real database, in
# one command, before you push. backend-migrate-check is deliberately
# excluded: it needs a real database, so it can't be part of an offline
# target — CI runs it separately, against a service container.
check: backend-lint backend-typecheck backend-test backend-check-destructive-migrations \
       backend-test-domain-coverage
