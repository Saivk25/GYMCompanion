# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) — see
`docs/RELEASE_PROCESS.md` for how that applies to a pre-1.0, not-yet-released project.

No version of this project has been tagged or released yet (`backend/pyproject.toml` and
`apps/mobile/pubspec.yaml` both currently read `0.1.0`). Everything below is grouped under
`[Unreleased]` until the first real release is cut. Entries reference the ADR that documents
the decision in full, rather than restating it here.

## [Unreleased]

### Added — Backend

- Framework-free Domain Layer for all eight aggregates: User, Workout, Exercise,
  WorkoutSession, Progress, Nutrition, Readiness, Goal (`docs/adr/0005`–`0012`).
- Nine deterministic Rule Engines: Readiness, Nutrition, Goal Alignment, Progressive Overload,
  Safety, Progress Evaluation, Training Load, Exercise Recommendation, plus the shared Rule
  Engine foundation (`docs/adr/0013`–`0021`).
- Application Layer (Commands/Queries/Handlers) for all eight aggregates, orchestration-only,
  with rule-engine output surfaced as advisory warnings, never a hard failure
  (`docs/adr/0022`–`0028`).
- Persistence Layer: SQLAlchemy models, Postgres row-level security, Alembic migrations
  (`docs/adr/0029`).
- Hand-rolled dependency-injection Composition Root and per-request `UnitOfWork`
  (`docs/adr/0030`).
- FastAPI API Layer: 37 REST endpoints across five modules (Workout, Nutrition, Progress,
  Readiness, Goal) (`docs/adr/0031`).
- Authentication & Authorization: JWT bearer tokens, bcrypt password hashing, refresh-token
  rotation, and per-resource ownership authorization across all 27 addressed-by-id routes
  (`docs/adr/0032`, `docs/adr/0033`).

### Added — Mobile (Flutter)

- Hand-tuned Design System: color/typography/spacing/motion tokens, light + dark themes, a
  closed component allow-list (`docs/adr/0034`, `docs/adr/0035`).
- Six feature modules, initially mock-backed: Today, Train, Fuel, Progress, Readiness, Coach
  (`docs/adr/0036`–`0041`).
- Production integration (`docs/adr/0042`): a real core networking layer (`docs/adr/0043`), a
  real Authentication module with automatic token refresh (`docs/adr/0044`), real
  `ApiXRepository` implementations replacing every mock repository across five features per a
  shared API-mapping convention (`docs/adr/0045`–`0051` — Coach confirmed to need no HTTP
  repository at all), a shared offline read-through cache with stale-while-revalidate
  (`docs/adr/0052`), a performance and accessibility audit (`docs/adr/0053`), and a
  testing/release-readiness validation pass (`docs/adr/0054`).
- A final, read-only end-to-end integration audit that found and fixed one genuine correctness
  bug (Today's "Start session" action pushing a hardcoded workout id) (`docs/adr/0055`).

### Added — Repository & tooling

- CI (`.github/workflows/ci.yml`): backend lint/format/typecheck, backend tests against a real
  Postgres service container, a Docker build smoke test, and `flutter analyze`/`flutter test`.
- Local developer tooling: `Makefile`, `pre-commit`, Docker Compose for local Postgres
  (`infra/`), a no-Docker local Postgres script (`scripts/local_postgres.sh`).
- 55 Architecture Decision Records (`docs/adr/`) and a running technical-debt backlog with
  explicit trigger conditions (`docs/TECH_DEBT.md`).
- Repository governance and contributor documentation: `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, `SECURITY.md`, issue/PR templates, `CODEOWNERS`, Dependabot
  configuration, and additional CI workflows (Markdown lint, spell check, dependency review,
  CodeQL, release).

### Known limitations

See `docs/TECH_DEBT.md` (14 tracked items) and `docs/ARCHITECTURE.md`'s "Known limitations"
section. Notably: no Flutter SDK has been available in this project's primary build
environment, so all Flutter code has been statically/structurally verified rather than run
(`docs/adr/0002`); no `android`/`ios` platform folders exist yet; no app has been submitted to
an app store; the backend has not been deployed anywhere live.

---

## Release history

_No releases yet._ The first tagged release will be `0.1.0` — see `docs/RELEASE_PROCESS.md`.
