# Architecture Decision Records

This directory records every non-trivial architectural decision made while building Gym
Companion, in the order they were made. All 55 records below are **Accepted** — none has been
superseded. New ADRs start from `template.md` and are numbered sequentially; nothing here is
renumbered or deleted after the fact, so the sequence itself is a real history, not a
snapshot.

For a synthesized, code-reflecting overview instead of the decision-by-decision log, start with
`docs/ARCHITECTURE.md`. Come back here when you need the *why* behind a specific choice.

## Foundations

| # | Title |
|---|---|
| [0001](0001-repository-layout.md) | Repository layout follows the Engineering Master Plan's Section 2 exactly |
| [0002](0002-flutter-verification-constraint.md) | Flutter code is hand-authored and verified structurally, not by running `flutter` |
| [0003](0003-flutter-state-management.md) | Riverpod for state management, no code generation in the MVP scaffold |
| [0004](0004-docker-verification-constraint.md) | Docker/Compose files are reviewed, not executed, in this environment |

## Backend — Domain Layer: aggregates

| # | Title |
|---|---|
| [0005](0005-user-aggregate-first-increment.md) | User aggregate, first increment |
| [0006](0006-workout-aggregate-first-increment.md) | Workout aggregate, first increment |
| [0007](0007-exercise-aggregate-first-increment.md) | Exercise aggregate, first increment |
| [0008](0008-workout-session-execution-record.md) | WorkoutSession — the execution record, split from Workout the plan |
| [0009](0009-exercise-performance-owned-entity.md) | ExercisePerformance/ExerciseSet are owned entities, not a separate aggregate |
| [0010](0010-progress-immutability-is-a-policy-not-a-guard.md) | Progress's "immutable after recording" rule is a policy, not a guard |
| [0011](0011-nutrition-is-a-per-entry-log-not-a-daily-rollup.md) | Nutrition is a per-entry log, not a daily rollup |
| [0012](0012-goal-lifecycle-and-expired-with-no-transition.md) | Goal's lifecycle and the EXPIRED value |

## Backend — Domain Layer: rule engines

| # | Title |
|---|---|
| [0013](0013-rule-engine-foundation.md) | Rule Engine foundation |
| [0014](0014-readiness-rule-composition.md) | Readiness Rule Engine |
| [0015](0015-nutrition-rules-use-range-thresholds.md) | Nutrition rules validate a `[min, max]` range |
| [0016](0016-goal-alignment-combines-whole-snapshots.md) | Goal Alignment Rule Engine |
| [0017](0017-progressive-overload-session-level-trends.md) | Progressive Overload Rule Engine |
| [0018](0018-safety-rule-engine-composition-and-authority.md) | Safety Rule Engine |
| [0019](0019-progress-evaluation-consistency-and-plateau-scope.md) | Progress Evaluation Rule Engine |
| [0020](0020-training-load-supplied-summaries.md) | Training Load Rule Engine |
| [0021](0021-exercise-recommendation-composes-rule-outputs.md) | Exercise Recommendation Rule Engine |

## Backend — Application Layer

| # | Title |
|---|---|
| [0022](0022-application-layer-foundation.md) | Application Layer Foundation |
| [0023](0023-user-application-use-cases.md) | User Application Use Cases |
| [0024](0024-workout-application-use-cases.md) | Workout Application Use Cases |
| [0025](0025-nutrition-application-use-cases.md) | Nutrition Application Use Cases |
| [0026](0026-progress-application-use-cases.md) | Progress Application Use Cases |
| [0027](0027-readiness-application-use-cases.md) | Readiness Application Use Cases |
| [0028](0028-goal-application-use-cases.md) | Goal Application Use Cases |

## Backend — Persistence, composition, API, auth

| # | Title |
|---|---|
| [0029](0029-persistence-layer.md) | Persistence Layer |
| [0030](0030-composition-root.md) | Composition Root |
| [0031](0031-fastapi-api-layer.md) | FastAPI API Layer |
| [0032](0032-authentication-and-authorization.md) | Authentication & Authorization |
| [0033](0033-resource-ownership-authorization.md) | Resource Ownership Authorization |

## Flutter — Design System

| # | Title |
|---|---|
| [0034](0034-flutter-design-system.md) | Flutter Design System |
| [0035](0035-design-system-refinement.md) | Design System Refinement |

## Flutter — feature modules (mock-backed, first build)

| # | Title |
|---|---|
| [0036](0036-today-screen.md) | Today screen |
| [0037](0037-train-module.md) | Train module |
| [0038](0038-fuel-module.md) | Fuel module |
| [0039](0039-progress-module.md) | Progress module |
| [0040](0040-readiness-module.md) | Readiness module |
| [0041](0041-coach-module.md) | Coach module |

## Production integration roadmap

| # | Title |
|---|---|
| [0042](0042-production-integration-plan.md) | Production integration plan (the roadmap itself — planning only) |
| [0043](0043-core-networking-layer.md) | Core networking layer — Step 1 |
| [0044](0044-authentication-module.md) | Authentication module — Step 2 |
| [0045](0045-shared-api-mapping-convention.md) | Shared API mapping convention |
| [0046](0046-today-repository-integration.md) | Today repository integration — Step 3 |
| [0047](0047-readiness-repository-integration.md) | Readiness repository integration — Step 3 |
| [0048](0048-train-repository-integration.md) | Train repository integration — Step 3 |
| [0049](0049-fuel-repository-integration.md) | Fuel repository integration — Step 3 |
| [0050](0050-progress-repository-integration.md) | Progress repository integration — Step 3 |
| [0051](0051-coach-repository-integration.md) | Coach repository integration — Step 3 (confirmed: no HTTP repository needed) |
| [0052](0052-offline-caching.md) | Offline caching — Step 4 |
| [0053](0053-performance-and-accessibility-audit.md) | Performance and accessibility audit — Step 5 |
| [0054](0054-testing-and-release-readiness.md) | Testing and release readiness — Step 6 (concludes the roadmap) |
| [0055](0055-final-integration-audit.md) | Final end-to-end integration audit |

## Writing a new ADR

1. Copy `template.md` to `NNNN-short-kebab-case-title.md`, using the next unused number.
2. Fill in Context / Decision / Consequences. Link related ADRs by number.
3. Add a row to the appropriate table above (or a new table, if this starts a new phase).
4. If the decision changes something `docs/TECH_DEBT.md` tracks, update or resolve that entry
   in the same change.
