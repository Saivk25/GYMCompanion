# Gym Companion

<!--
CI badge: this repository doesn't have a GitHub remote configured yet
(everything so far has been built and committed locally). Once it's pushed
to GitHub, uncomment the line below and replace OWNER/REPO — GitHub Actions
generates this badge URL automatically from .github/workflows/ci.yml, no
separate setup needed.
[![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/ci.yml)
-->

A private, AI-assisted fitness operating system — not a workout tracker, not a calorie
counter, not a chatbot. Built first for one user, generalized later only once proven.

This repository is the implementation of the six frozen planning documents in `docs/`.
**Those documents are the source of truth for product and architecture decisions.** This
README only orients you around the code; it does not restate product behavior.

## Reading order (if you are new here)

1. `docs/Gym_Companion_Design_Document.docx` — the personal record this product is built from.
2. `docs/Gym_Companion_System_Architecture.docx` — critical review and technical architecture.
3. `docs/Gym_Companion_Product_Bible.docx` — the complete, prioritized feature catalog.
4. `docs/Gym_Companion_Domain_Model_Decision_Engine_Bible.docx` — entities, workflows, state
   machines, the decision engine, the event system, the rule engines.
5. `docs/Gym_Companion_UX_UI_Design_Bible.docx` — every screen, flow, and interaction.
6. `docs/Gym_Companion_Engineering_Master_Plan.docx` — how the above becomes working software,
   in what order, for a solo developer first.

## Repository layout

| Path | Purpose |
|---|---|
| `apps/mobile/` | The Flutter client — one app, five tabs, per the UX/UI Design Bible. |
| `backend/` | The FastAPI service. `app/domain/` is framework-free business logic; everything else is a thin layer around it. |
| `infra/` | Local development infrastructure (Docker Compose for Postgres + backend). No Kubernetes — see the Engineering Master Plan's over-engineering table for why. |
| `.github/workflows/` | CI only (lint, typecheck, tests, migrations, Docker build, Flutter analyze/test). No deployment workflow exists yet — see the Engineering Master Plan Section 10, release process is manual during MVP through Beta. |
| `docs/` | The six planning documents plus `adr/` for architecture decision records raised during implementation. |
| `scripts/` | One-off developer scripts (database seeding, environment bootstrap, local Postgres, CI-adjacent checks). |
| `tests/e2e/` | Full-stack end-to-end tests spanning the mobile app and backend together. Unit/widget/integration tests live inside `apps/mobile/test/` and `backend/tests/` respectively. |
| `assets/` | Shared design assets referenced by the UX/UI Design Bible (icons, fonts) — not yet populated. |
| `datasets/`, `models/` | Reserved for future use if a custom model is ever justified. Per the Engineering Master Plan, no custom model training is planned for MVP through v1 — these exist so the layout doesn't need to change if that ever becomes justified. |

## Status

Sprint 1 (environment setup) of the Engineering Master Plan is complete: repository
structure, backend and Flutter scaffolds, tooling, testing, linting, formatting, Docker,
Postgres, Alembic, CI, and the framework-independent Domain Core skeleton
(`backend/app/domain/shared_kernel/` — see `backend/README.md`'s "Domain Core" section)
are all done (Steps 1–12).

Sprint 2's aggregates are implemented: `User`, `Workout`, `Exercise`,
`WorkoutSession`, `Progress`, `Nutrition`, `Readiness`, and `Goal`
(`backend/app/domain/user/`, `backend/app/domain/workout/`,
`backend/app/domain/exercise/`, `backend/app/domain/workout_session/`,
`backend/app/domain/progress/`, `backend/app/domain/nutrition/`,
`backend/app/domain/readiness/`, `backend/app/domain/goal/` — see
`backend/README.md`'s "Domain aggregates" section). No persistence
(SQLAlchemy model, repository implementation, migration) exists for any of
them yet — domain logic only.

Sprint 3, Phase 1 is done: the reusable Rule Engine foundation
(`backend/app/domain/rules/` — see `backend/README.md`'s "Rule Engine
foundation" section) that every future deterministic rule engine builds
on. No fitness-specific rules exist yet — this phase implemented only the
shared architecture (`Rule`, `RuleEngine`, `RuleContext`, `RuleResult`,
`Recommendation`, `RecommendationSeverity`).

Sprint 3, Phase 2 is done: the Readiness Rule Engine
(`backend/app/domain/readiness/rules/` — see `backend/README.md`'s
"Readiness Rule Engine" section), the first of the Bible's nine concrete
rule engines — five independent rules (sleep, energy, stress, soreness,
recovery metrics) evaluating a `Readiness` check-in and producing
deterministic `Recommendation`s.

Sprint 3, Phase 3 is done: the Nutrition Rule Engine
(`backend/app/domain/nutrition/rules/` — see `backend/README.md`'s
"Nutrition Rule Engine" section), the second — six independent rules
(calories, protein, carbohydrates, fat, fiber, hydration), each
validating its field against a configurable range, evaluating a
`Nutrition` entry and producing deterministic `Recommendation`s.

Sprint 3, Phase 4 is done: the Goal Alignment Rule Engine
(`backend/app/domain/goal/rules/` — see `backend/README.md`'s "Goal
Alignment Rule Engine" section), the first rule engine spanning two
aggregates (`Goal` and `Progress`) — five independent rules (target
date, body weight, body fat, strength-data-sufficiency, priority)
evaluating whether a user's current state aligns with an active goal.

Sprint 3, Phase 5 is done: the Progressive Overload Rule Engine
(`backend/app/domain/workout/rules/` — see `backend/README.md`'s
"Progressive Overload Rule Engine" section), the first rule engine
evaluating a history of snapshots rather than one point in time — five
independent rules (volume, intensity, frequency, progression, deload)
evaluating training trends across a user's `WorkoutSession` history.

Sprint 3, Phase 6 is done: the Safety Rule Engine
(`backend/app/domain/safety/rules/` — see `backend/README.md`'s "Safety
Rule Engine" section), the first rule engine with no aggregate of its
own — it composes two other engines' context types (Readiness,
Progressive Overload) instead — five independent rules (readiness
safety, soreness, workload spike, contraindication, injury) evaluating
whether it is currently safe for a user to train.

Sprint 3, Phase 7 is done: the Progress Evaluation Rule Engine
(`backend/app/domain/progress/rules/` — see `backend/README.md`'s
"Progress Evaluation Rule Engine" section), the first context to combine
a history of snapshots with a whole referenced snapshot at once — five
independent rules (body weight trend, body fat trend, measurement trend,
consistency, plateau) evaluating whether a user's historical
body-composition trends are progressing toward an active goal.
`ConsistencyRule` is the first rule in the codebase to deliberately fail
(rather than pass) on missing or stale data, grounded in the Bible's
"Minimum evidence rule."

Sprint 3, Phase 8 is done: the Training Load Rule Engine
(`backend/app/domain/training_load/rules/` — see `backend/README.md`'s
"Training Load Rule Engine" section), the first package whose context
builds no summaries of its own at all — every `TrainingLoadSummary` is
supplied pre-computed by the application layer — five independent
rules (acute load, chronic load, acute:chronic load ratio, monotony,
strain) evaluating accumulated training load using sports-science
concepts (Foster's monotony/strain, the acute:chronic workload ratio)
the Bible names only implicitly, as an input to `RecoveryState`, not by
these terms directly.

Sprint 3, Phase 9 is done: the Exercise Recommendation Rule Engine
(`backend/app/domain/exercise/rules/` — see `backend/README.md`'s
"Exercise Recommendation Rule Engine" section), the first engine that
orchestrates other engines' *already-computed* `RuleResult` outputs
(Safety, Readiness) rather than their raw inputs — five independent
rules (exercise selection, contraindicated exercise, movement balance,
equipment, progression stage) recommending whether one candidate
`Exercise` fits a user's goal, safety restrictions, available
equipment, recent movement pattern balance, and training experience.
Only `ContraindicatedExerciseRule` and `EquipmentRule` — the Bible's
Table 48 "removed from candidates" gates — can exclude a candidate; the
other three are pure advisory biases, matching Table 48's "biases...
ranking" language. Of the Bible's nine named engines, Workout, Recovery
scoring, Recommendation, Notification, Analytics, and AI Validation are
still ahead.

Sprint 3 is complete: all nine Rule Engines are implemented, tested to
100% domain coverage, and committed.

Sprint 4, Phase 1 is done: the Application Layer Foundation
(`backend/app/application/shared/` — see `backend/README.md`'s
"Application Layer Foundation" section), the shared orchestration
contracts (`Command`, `Query`, `CommandHandler`, `QueryHandler`,
`ApplicationResult`, `Repository`, `UnitOfWork`,
`DomainEventDispatcher`, application-specific exceptions) every future
use case will depend on. No use case, concrete repository,
SQLAlchemy, FastAPI, or AI integration exists yet — this phase
implemented only the framework-independent orchestration contracts
sitting between the Domain Layer and future infrastructure. See
`docs/adr/` for decisions made during implementation that weren't
already pinned down by the six planning documents.

## Getting started

- Backend: `backend/README.md`
- Mobile: `apps/mobile/README.md`
- Local Postgres + backend together: `infra/README.md`
