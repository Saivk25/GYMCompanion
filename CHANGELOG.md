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

### Fixed

- The first real `flutter analyze`/`flutter test` run against this codebase, on a developer
  machine with a real Flutter SDK (`docs/adr/0002`'s "Update" note): fixed 61 pre-existing lint
  issues, 6 real test bugs, and one genuine application bug (`active_workout_screen.dart`'s
  `pushReplacement` to session summary was missing `extra: true`). Result: 0 analyzer issues,
  303/303 tests passing.
- Closed 4 tracked tech-debt items found during the performance/accessibility audit
  (`docs/TECH_DEBT.md` TD-0004, TD-0010, TD-0012, TD-0013): consolidated duplicated date/
  duration formatting into one shared helper; converted `ReadinessTimelineScreen` to a
  genuinely lazy `ListView.builder`; fixed `LoggedSetRow`'s sub-48dp tap target; added keyboard
  focus chaining to three multi-field forms.
- Widened `test/accessibility/guideline_test.dart` from 2 representative screens to 28 of this
  app's 29 screens (TD-0014), which itself caught and fixed two further real bugs: Active
  Workout's Weight/Reps/RPE fields were also under the 48dp tap-target minimum, and one new
  guideline test's own pump timing was reading a still-transitioning route as a false contrast
  failure.

### Known limitations

See `docs/TECH_DEBT.md` (14 tracked items — 7 resolved, 1 partially resolved, 6 open) and
`docs/ARCHITECTURE.md`'s "Known limitations" section. Notably: `flutter analyze`/`flutter test`
now run clean on a real machine, but the app itself has never run on a real device or simulator
(`docs/adr/0002`); no app has been submitted to an app store; the backend has not been deployed
anywhere live.

---

## Release history

_No releases yet._ The first tagged release will be `0.1.0` — see `docs/RELEASE_PROCESS.md`.
