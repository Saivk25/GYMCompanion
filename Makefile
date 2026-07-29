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
check: backend-lint backend-typecheck backend-test
