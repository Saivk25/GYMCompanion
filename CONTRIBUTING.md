# Contributing to Gym Companion

Thanks for your interest in this project. This repository is currently maintained by a single
developer and evolved as a portfolio/personal project, so the process below is intentionally
lightweight — it exists to keep the codebase's own architectural discipline (Clean Architecture,
documented decisions, no undocumented shortcuts) intact as it grows, not to gatekeep.

## Before you start

Read `README.md` for the project overview, then `docs/ARCHITECTURE.md` for how the pieces fit
together. If you're touching a specific area, skim the relevant ADR(s) in `docs/adr/` (index:
`docs/adr/README.md`) — most non-obvious decisions in this codebase are already explained there,
and re-litigating a decision that already has a documented rationale wastes everyone's time.
`docs/TECH_DEBT.md` lists every known, deliberately-deferred gap with its own trigger condition
for when to act on it — check it before assuming something is an oversight.

## Project structure

- `backend/` — FastAPI service, Clean Architecture (`domain/ → application/ → infra/ → api/`).
  See `backend/README.md`.
- `apps/mobile/` — Flutter client, the same layering per feature. See `apps/mobile/README.md`.
- `docs/adr/` — Architecture Decision Records. Every non-trivial design choice gets one.
- `docs/TECH_DEBT.md` — tracked, deliberately-deferred technical debt with concrete trigger
  conditions, not a general TODO list.

## Development setup

**Backend:**

```bash
cd backend
python3 -m venv ~/.venvs/gym-backend
~/.venvs/gym-backend/bin/pip install -e ".[dev]"
cp .env.example .env   # adjust GYM_DATABASE_URL once Postgres is available
```

Or from the repository root, via the Makefile:

```bash
make backend-install       # editable install, dev extras
make precommit-install     # wires pre-commit into git
```

**Mobile:**

```bash
cd apps/mobile
flutter pub get
```

Or `make mobile-get` from the repository root. `docs/adr/0002-flutter-verification-constraint.md`
records that this repo's own primary build environment has no Flutter SDK available — if you're
working from a machine that does, you have first-class verification the original author didn't
during large parts of this project's history. Use it: `flutter analyze` and `flutter test` should
both be run locally before opening a PR, not just left to CI.

## Making a change

1. **Open an issue first** for anything beyond a trivial fix (typo, obviously broken link) —
   see the issue templates under `.github/ISSUE_TEMPLATE/`. This avoids duplicated work and
   surfaces design disagreements before code is written, not after.
2. **Branch from `master`.** There is no separate `develop` branch — `master` is always
   releasable, per `docs/RELEASE_PROCESS.md`.
3. **Follow the existing layering.** Business logic belongs in `domain/` (backend) or a
   feature's `domain/`/`application/` (Flutter) — never in a route handler, a repository, or a
   widget. If you're unsure where something belongs, check how the nearest analogous concept is
   already organized before inventing a new pattern.
4. **Write tests.** Backend: `pytest`, with 100% coverage enforced on `app.domain` in CI.
   Mobile: `flutter test`, following the existing hand-rolled-fake convention (no mocking
   framework — see any existing `test/features/*/*.dart` file for the pattern).
5. **Run the local quality gate** before opening a PR:

   ```bash
   make backend-lint          # ruff check
   make backend-format        # ruff format
   make backend-typecheck     # mypy --strict
   make backend-test          # pytest
   make mobile-analyze        # flutter analyze
   make mobile-test           # flutter test
   ```

   `pre-commit install` (`make precommit-install`) runs a fast subset of this automatically on
   every commit.
6. **Document real architectural decisions.** If your change makes a non-obvious trade-off,
   add an ADR (`docs/adr/`, use `docs/adr/template.md`) rather than leaving the reasoning only
   in a commit message or a PR description that will be harder to find later.
7. **Open a pull request** using the template. Link the issue it closes. Keep the diff scoped to
   one concern — this project's own history (see `docs/adr/`) consistently treats "one phase, one
   scoped unit of work" as the default, not an exception.

## Code style

- **Backend (Python):** `ruff` for linting and formatting, `mypy --strict` for types. Configured
  in `backend/pyproject.toml`. No unused `noqa`, no `# type: ignore` without a comment explaining
  why.
- **Mobile (Dart):** `flutter analyze` against `apps/mobile/analysis_options.yaml`. No
  code-generation-dependent packages without a real justification — see `docs/adr/0003`.
- **Everything else:** `.editorconfig` at the repository root sets whitespace/indentation
  defaults; most editors pick it up automatically.

## Commit messages

Short, imperative subject line; a body explaining *why*, not just *what*, for anything non-
trivial — the existing commit history in this repository is itself the convention to follow.

## Reporting bugs and requesting features

Use the issue templates under `.github/ISSUE_TEMPLATE/`. For anything security-related, **do
not** open a public issue — see `SECURITY.md`.

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). By participating, you're
expected to uphold it.
