# Gym Companion — backend

FastAPI service over a framework-free domain core. See `docs/Gym_Companion_Engineering_Master_Plan.docx`
(repository root) for the full rationale; this file only covers running the code.

## Layout

- `app/domain/` — framework-free business logic (entities, state machines, rule engines).
  Depends on nothing outside the Python standard library — not `api/`, not `infra/`, not
  even `pydantic` — enforced by a static test, not just convention (see "Domain Core"
  below). `app/domain/shared_kernel/` is the base-type toolkit every future aggregate
  builds on (Sprint 2 onward); no per-aggregate business logic exists yet.
- `app/api/` — thin FastAPI routers and Pydantic schemas over `app/domain/`.
- `app/ai/` — the AI Adapter Layer (vendor-agnostic vision/language provider interfaces).
  Empty until Sprint 1 (Alpha milestone) per the Engineering Master Plan.
- `app/infra/` — SQLAlchemy models, repositories, the only place that knows about Postgres.
  `database.py` owns the engine/session and the row-level-security convention (`tenant_scope`);
  see its docstring before writing any query that touches per-user data. `models.py` holds
  the ORM mapping classes (persistence shape only — not the Domain Core). `orm_base.py`
  holds the shared declarative base and naming convention Alembic autogenerate relies on.
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

For a reproducible install that matches exactly what CI ran — the exact, hash-pinned
dependency versions in `requirements-lock.txt`, rather than pyproject.toml's ranges
resolved fresh — use `make backend-install-locked` instead. See "Reproducible builds"
below.

Copy `.env.example` to `.env` and adjust `GYM_DATABASE_URL` once Postgres is available.

Run the API:

```bash
uvicorn app.main:app --reload
```

Run the tests:

```bash
pytest
```

## Postgres

Two ways to get a local Postgres for development, either works:

- **Docker Compose** (simplest if you have Docker): `cd infra && docker compose up` — see
  `infra/README.md`.
- **`scripts/local_postgres.sh`** (no Docker required, uses your system's installed Postgres):
  ```bash
  scripts/local_postgres.sh start
  ```
  This initializes a data directory under `~/.gym-companion/pgdata` on first run, and creates
  the `gymcompanion` role/database. It prints the connection URL to export as
  `GYM_DATABASE_URL` (for running the app) and `GYM_TEST_DATABASE_URL` (for running the
  integration tests below). Stop it with `scripts/local_postgres.sh stop`.

### Row-level security convention

Every per-tenant table is protected by a Postgres RLS policy keyed on the session variable
`app.current_user_id`. `app/infra/database.py`'s `tenant_scope()` context manager is the
**only** place in the codebase allowed to set it — application code must never filter
per-user tables by `user_id` in a `WHERE` clause as a substitute for RLS. This is a
"never do this" rule, not a style preference: see the Architecture document's Section 19
and `app/infra/database.py`'s docstring for why.

### Integration tests

`tests/infra/` contains tests that need a real Postgres connection
(`@pytest.mark.integration`). They read `GYM_TEST_DATABASE_URL` (falling back to the same
default as `GYM_DATABASE_URL`) and **skip themselves with a clear reason** — they do not
fail the suite — if no Postgres is reachable. Point `GYM_TEST_DATABASE_URL` at a throwaway
database, never at one with real data.

## Database migrations (Alembic)

```bash
make backend-migrate              # apply every migration up to head
make backend-migrate-down         # revert exactly one migration
make backend-migration m="add profile table"   # autogenerate a new migration
make backend-migrate-check        # fail if models.py and the latest migration have drifted
```

All four read the target database from `GYM_DATABASE_URL` — same variable, same `.env`,
as the running app. There is no separate migrations config to keep in sync.

Workflow for a schema change: edit `app/infra/models.py`, run `make backend-migration
m="..."`, **read the generated file** in `alembic/versions/` before committing it —
autogenerate detects table/column/constraint changes but knows nothing about row-level
security, which must be added by hand in the migration (see
`alembic/versions/..._create_users_table_with_row_level_.py` for the pattern: `ENABLE
ROW LEVEL SECURITY`, `FORCE ROW LEVEL SECURITY`, then `CREATE POLICY`), then run `make
backend-migrate` against a real database and confirm it applies cleanly before opening a
PR.

Naming: migration files are timestamp-prefixed (`alembic.ini`'s `file_template`) so
`alembic/versions/` sorts chronologically. Constraint/index names come from a fixed
naming convention (`app/infra/orm_base.py`) so autogenerated names are deterministic
rather than Postgres-assigned. Every autogenerated file is run through `ruff format` and
`ruff check --fix` automatically (`alembic.ini`'s `post_write_hooks`), so it never fails
`make check` on its own.

### A hard-won RLS + migrations lesson

Two things about `FORCE ROW LEVEL SECURITY` are not obvious and both were caught only by
testing against a real database, not by reading the code:

1. A policy with no explicit `WITH CHECK` reuses its `USING` expression for inserts too —
   which means the *first* row in a tenant-root table (an account signup) can never be
   inserted, since there's no tenant to check against yet. The `users` migration's policy
   has `WITH CHECK (true)` specifically to allow this.
2. `WITH CHECK (true)` only covers a bare `INSERT`. An `INSERT ... RETURNING` — the normal
   ORM pattern — also reads the new row back, and that read is governed by `USING`, not
   `WITH CHECK`. The correct application-level pattern (documented on `UserAccount` in
   `app/infra/models.py`) is to generate the new user's id in Python and call
   `tenant_scope(session, str(new_id))` *before* inserting, so the id already matches by
   the time Postgres evaluates `RETURNING`. `tests/infra/test_migrations.py`'s
   cross-tenant test exercises exactly this pattern.

## Reproducible builds

`requirements-lock.txt` pins every dependency (direct and transitive) to an exact,
hash-verified version. CI (`.github/workflows/ci.yml`) installs from this file, not from
`pyproject.toml`'s ranges — so a build today and a build in six months resolve to
identical versions, until someone deliberately regenerates the lock file:

```bash
make backend-lock                 # regenerate after changing a dependency
make backend-install-locked       # install exactly what's locked (what CI does)
```

Review the diff before committing a regenerated lock file — it's the only way a
dependency bump becomes visible in code review, since `pyproject.toml`'s own ranges
often don't change at all when only a transitive dependency moves.

## Domain Core

`app/domain/shared_kernel/` is the framework-independent foundation every real aggregate
(Sprint 2 onward) is built from — not business logic itself, but the base types that make
writing it consistent:

| Module | Provides |
|---|---|
| `identifiers.py` | `EntityId` — subclass per aggregate (`class UserId(EntityId)`) for compile-time-checked, non-interchangeable ids. |
| `clock.py` | `Clock` / `SystemClock` / `FixedClock` — time as an injected dependency, never a bare `datetime.now()` call. |
| `value_object.py` | `ValueObject` — immutable, equality-by-value base; frozen-dataclass inheritance makes forgetting `frozen=True` a `TypeError` at import time, not a runtime bug. |
| `entity.py` | `Entity` — identity-based (not field-based) equality and hashing. |
| `aggregate_root.py` | `AggregateRoot` — adds the domain-event recording/draining lifecycle on top of `Entity`. |
| `events.py` | `DomainEvent` — immutable, `occurred_at`-stamped record of something that already happened. |
| `errors.py` | `DomainError` (an expected, returnable failure) vs. `DomainInvariantViolationError` (a raised bug) — see the module docstring for the distinction. |
| `result.py` | `Ok[T]` / `Err[E]` — expected failures as values instead of exceptions. |
| `repository.py` | `Repository[TAggregate, TId]` — the persistence contract `app/infra/` implements; domain code depends on this interface, never on SQLAlchemy. |
| `service.py` | `DomainService` — marker base for stateless cross-aggregate logic (the nine rule engines, starting Sprint 2+). |
| `validation.py` | `ensure()` / `ensure_not_empty()` / `ensure_positive()` — guard clauses that raise `DomainInvariantViolationError`. |

Every name is re-exported from `app.domain.shared_kernel` directly, so real aggregate
code writes one import instead of several — see that package's `__init__.py`.

### The one architecture rule, enforced statically

"Domain depends on nothing but the Python standard library" is not just documented — it's
a real test. `tests/domain/test_import_boundaries.py` parses every file under
`app/domain/` with `ast` and checks every import's target against
`sys.stdlib_module_names` (a positive allow-list, so a *new* forbidden dependency is
caught automatically, not just the ones anyone thought to ban). This runs as part of the
normal test suite and again as CI's own dedicated gate — see below.

```bash
make backend-test-domain-coverage   # import-boundary test + 100%-coverage gate, domain only
```

`app/domain` carries its own, stricter, 100%-coverage requirement, separate from the rest
of the backend (`pyproject.toml`'s `[tool.coverage.report]` explains why it can't just be
one repo-wide number) — matching the Engineering Master Plan's testing strategy table:
"Domain Core ... near-100% coverage ... merge-blocking."

## Domain aggregates

Real, product-specific aggregates, built on the Domain Core above. One
package per aggregate under `app/domain/`, mirrored 1:1 by `tests/domain/`.

| Aggregate | Package | Bible reference |
|---|---|---|
| User | `app/domain/user/` | Section 4.1 (User / Account). `UserProfile` is a value object here, not the Bible's standalone `Profile` aggregate (Section 4.2) — see `docs/adr/0005-user-aggregate-first-increment.md` for why and the migration path. No persistence exists for this aggregate yet: no ORM model, no repository implementation, no migration. |
| Workout | `app/domain/workout/` | Closest to Section 4.7 (`WorkoutSession`), but a standalone aggregate — no owning `WorkoutPlan`/`WorkoutTemplate`, no `ExerciseSet` — with a simpler four-state lifecycle (`Planned`/`InProgress`/`Completed`/`Cancelled`) than the Bible's five. See `docs/adr/0006-workout-aggregate-first-increment.md`. No persistence yet, same as User. |
| Exercise | `app/domain/exercise/` | Closest to Section 4.5 (`ExerciseGraph`), but the catalog node only — no `ExerciseRelation`, no graph traversal — with a simpler two-state lifecycle (`Active`/`Deprecated`) than the Bible's four. Unlike User and Workout, carries no `user_id`: a shared, global catalog, not tenant-scoped. See `docs/adr/0007-exercise-aggregate-first-increment.md`. No persistence yet. |
| WorkoutSession | `app/domain/workout_session/` | Closest to Section 4.7 (`WorkoutSession`, Table 10) — the execution record of a `Workout`, referenced by `workout_id` only. Four-state lifecycle (`Planned`/`Active`/`Completed`/`Abandoned`) versus the Bible's five, and `plan()` raises no creation event, unlike every other aggregate's factory. Owns `ExercisePerformance` (entity) and `ExerciseSet` (value object) — what was actually performed, exercise by exercise, set by set — as child objects with no repository of their own. See `docs/adr/0008-workout-session-execution-record.md` and `docs/adr/0009-exercise-performance-owned-entity.md`. No persistence yet. |
| Progress | `app/domain/progress/` | Closest to Section 4.10 (`Measurement`, Table 13), broadened to cover body composition (`BodyFatPercentage`/`LeanBodyMass`/`MuscleMass`) and two extra tape sites (`Calf`/`Neck`) beyond the Bible's own weight/waist/hip/chest/arm/thigh list. No status enum and no lifecycle — a check-in is a fact, not a workflow. "Immutable after recording" is documented policy, not a domain-layer guard: `update_body_composition`/`update_measurements`/`update_notes` are real, unconditionally-callable mutations. See `docs/adr/0010-progress-immutability-is-a-policy-not-a-guard.md`. No persistence yet. |
| Nutrition | `app/domain/nutrition/` | Closest to Section 4.9 (`Meal`, "a single logged eating event", Table 12), scoped down to canonical storage only — no AI assessment, `FoodItem` references, or Logged/Assessed/Confirmed/Disputed lifecycle. One record per logged entry, not a daily rollup; `meal_type`/`source` are both optional. See `docs/adr/0011-nutrition-is-a-per-entry-log-not-a-daily-rollup.md`. No persistence yet. |
| Readiness | `app/domain/readiness/` | Closest to Section 4.8 (`ReadinessCheckIn`, "today's snapshot", Table 11). Stores observations only — no readiness/recovery score, deload triggers, or anything derived from a window of check-ins (that's `RecoveryState`, not built yet). Adds `RestingHeartRate`/`HeartRateVariability` beyond the Bible's own sleep/stress/soreness list; `pain_flags`/`GI_symptoms` are deliberately not modeled (routed through `SafetyFlag` in the Bible, a separate aggregate not built yet). The Bible's "one check-in per day" rule is not enforced at the domain layer — an application/repository-layer concern, same as every other aggregate's uniqueness constraints. No persistence yet. |
| Goal | `app/domain/goal/` | Closest to Section 4.4 (`Goal`, Table 6), with a four-state lifecycle (`Active`/`Completed`/`Cancelled`/`Expired`) simplified from the Bible's own six-state model (`Proposed -> Active -> Achieved / Abandoned / Superseded -> Archived`, Section 7.4). `GoalStatus.EXPIRED` is a legal status value with no method that transitions into it — no `GoalExpired` event was named for this increment. No priority-ranking or conflict-resolution logic across a user's concurrent goals is implemented. See `docs/adr/0012-goal-lifecycle-and-expired-with-no-transition.md`. No persistence yet. |

## Rule Engine foundation

Sprint 3, Phase 1's shared infrastructure (`app/domain/rules/`, mirrored by
`tests/domain/rules/`) that every future deterministic rule engine builds
on — Bible Section 8.1's "Deterministic Rule Layer" and Section 10's nine
named engines (Workout, Nutrition, Recovery, Safety, Recommendation,
Notification, Progress, Analytics, AI Validation), none of which are built
yet. This phase implements no fitness-specific logic at all.

`Rule[TContext]` (abstract; concrete rules subclass it and implement only
`evaluate()`) and `RuleEngine[TContext]` (evaluates a fixed, ordered set
of rules against one `TContext` and aggregates their outcomes) are both
generic over `RuleContext` — an intentionally empty marker base class each
future engine's own context subclasses. `RuleResult` is deliberately one
type used identically whether it's a single rule's outcome or
`RuleEngine.evaluate()`'s aggregated outcome. `RuleId` is a plain,
non-empty string (not the shared kernel's UUID-based `EntityId`) because
rules are code-defined, versioned instances, not runtime-created
aggregates. No `repository.py` — rules aren't persisted. See
`docs/adr/0013-rule-engine-foundation.md` for the full reasoning behind
all of these.

## Readiness Rule Engine

Sprint 3, Phase 2's first concrete rule engine
(`app/domain/readiness/rules/`, mirrored by
`tests/domain/readiness/rules/`), built on the Rule Engine foundation
above and the Readiness aggregate. Evaluates a `ReadinessRuleContext`
(sleep duration, energy/stress/soreness levels, resting heart rate, and
heart rate variability — only the six fields readiness rules need, not
the full aggregate) against five independent rules — `SleepRule`,
`EnergyRule`, `StressRule`, `SorenessRule`, `RecoveryRule` (the one rule
spanning two fields: resting heart rate and HRV) — each with its own
configurable threshold and severity, defaulting to this phase's own
general-purpose figures (7h sleep, energy/stress/soreness at 4/7/7 out of
10, 70 bpm resting heart rate, 40 ms HRV). A missing input is treated as
"nothing to flag," never a failure. `ReadinessRuleEngine` composes all
five by default via the shared `RuleEngine[ReadinessRuleContext]` — a
thin, behavior-preserving subclass that only wires up the default rule
set. Produces no recovery score, fatigue score, or training load — see
`docs/adr/0014-readiness-rule-composition.md` for why independent rules
were chosen over one monolithic evaluator, and for the reasoning behind
every other design choice in this package.

## Nutrition Rule Engine

Sprint 3, Phase 3's second concrete rule engine
(`app/domain/nutrition/rules/`, mirrored by
`tests/domain/nutrition/rules/`), built on the Rule Engine foundation and
the Nutrition aggregate, following the same independent-rule composition
strategy ADR 0014 established. Evaluates a `NutritionRuleContext`
(calories, protein, carbohydrates, fat, fiber, water intake — only the
six fields nutrition rules need, not the full aggregate, and notably not
`sugar`) against six independent rules — `CaloriesRule`, `ProteinRule`,
`CarbohydratesRule`, `FatRule`, `FiberRule`, `HydrationRule` — each
validating its field against a configurable `[minimum, maximum]` range
(unlike Readiness's single-sided thresholds — see
`docs/adr/0015-nutrition-rules-use-range-thresholds.md` for why), with
generic single-day sanity defaults (e.g. 1200-4000 kcal, 50-250 g
protein). A missing input is treated as "nothing to flag," never a
failure. `NutritionRuleEngine` composes all six by default via the shared
`RuleEngine[NutritionRuleContext]` — a thin, behavior-preserving subclass
that only wires up the default rule set. Produces no meal plans, food
database lookups, macro recommendations, or personalized calorie
targets.

## Goal Alignment Rule Engine

Sprint 3, Phase 4's third concrete rule engine
(`app/domain/goal/rules/`, mirrored by `tests/domain/goal/rules/`), the
first spanning two aggregates. `GoalAlignmentRuleContext` references
whole `GoalContext` and optional `ProgressContext` snapshots — unlike
Readiness's/Nutrition's flattened contexts — plus an explicit
`reference_date` (never a wall-clock read; see
`docs/adr/0016-goal-alignment-combines-whole-snapshots.md`). Five
independent rules — `TargetDateRule` (approaching/overdue),
`BodyWeightRule` and `BodyFatRule` (current vs. target, within a
configurable tolerance, each passing on missing data),
`StrengthGoalRule` (always passes — this context carries no strength
performance data yet), `PriorityRule` (highlights high-priority goals) —
all share one guard: a goal that isn't Active always passes. Produces no
workout planning, progressive overload, exercise recommendations,
training load, or nutrition advice.

## Progressive Overload Rule Engine

Sprint 3, Phase 5's fourth concrete rule engine
(`app/domain/workout/rules/`, mirrored by `tests/domain/workout/rules/`),
the first evaluating a *history* of snapshots rather than one point in
time. `ProgressiveOverloadRuleContext` holds pre-computed
`WorkoutSessionSummary` values — one per `Completed` `WorkoutSession`,
each summarizing whole-session `total_volume` (sum of weight x reps) and
`average_load` (mean set weight), built once via
`from_session_contexts()` so no rule re-derives these numbers from raw
`ExerciseSet` data itself. Five independent rules — `VolumeRule` and
`IntensityRule` (flag a declining average trend between the earlier and
later half of the evaluated history), `FrequencyRule` (flags a sessions-
per-week rate below a configurable minimum, computed from the session
history's own date span, no wall clock), `ProgressionRule` (flags no new
*peak* volume or load at all — a plateau, distinct from a decline),
`DeloadRule` (flags a trailing run of sessions all near the historical
peak volume with no lighter session — a workout-volume-only heuristic,
not the Bible's Recovery-Rules deload trigger, which needs
`RecoveryState`/`ReadinessCheckIn` data this phase doesn't have) — see
`docs/adr/0017-progressive-overload-session-level-trends.md` for the full
reasoning, including the stated whole-session/mixed-exercise
simplification every volume/load number carries.
`ProgressiveOverloadRuleEngine` composes all five by default via the
shared `RuleEngine[ProgressiveOverloadRuleContext]`. Produces no workout
generation, exercise substitution, fatigue scoring, or scheduling.

## Safety Rule Engine

Sprint 3, Phase 6's fifth concrete rule engine
(`app/domain/safety/rules/`, mirrored by `tests/domain/safety/rules/`),
the first with no aggregate of its own — no `SafetyFlag` aggregate
exists yet, so `app/domain/safety/` holds only this rules package.
`SafetyRuleContext` composes two other engines' whole context types
(`readiness: ReadinessContext | None`, `recent_training:
ProgressiveOverloadRuleContext | None`) plus two small, new value
objects no aggregate carries yet (`DeclaredRestriction`, `ActiveInjury`
— "supplied in the context" per this phase's own task, since no
`SafetyFlag` aggregate exists to source them from). Five independent
rules — `ReadinessSafetyRule` and `SorenessRule` (CRITICAL-severity red
flags from sleep/stress/heart-rate/soreness signals, stricter than and
deliberately independent of Readiness's own advisory rules on the same
fields), `WorkloadRule` (flags a sudden training-volume spike relative
to a recent baseline — a "too much, too soon" injury-risk pattern,
distinct from Progressive Overload's `DeloadRule`), `ContraindicationRule`
(surfaces declared restrictions on file, ADVISORY — ​can only say a
restriction exists, never that a specific exercise violates it),
`InjuryRule` (CRITICAL when any active injury still restricts training)
— see `docs/adr/0018-safety-rule-engine-composition-and-authority.md`
for the full reasoning, including this engine's evaluation-only
authority: it computes findings, it cannot itself block a session or
override another engine's output. `SafetyRuleEngine` composes all five
by default via the shared `RuleEngine[SafetyRuleContext]`. Produces no
exercise substitution, workout planning or generation, or AI coaching.

## Progress Evaluation Rule Engine

Sprint 3, Phase 7's sixth concrete rule engine
(`app/domain/progress/rules/`, mirrored by
`tests/domain/progress/rules/`), the first context to combine a
*history* of snapshots (`progress_history: tuple[ProgressContext, ...]`,
Progressive Overload's shape) with a *whole referenced snapshot*
(`goal: GoalContext | None`, Goal Alignment's shape) at the same time —
needed because `BodyWeightRule`/`BodyFatRule` compare a trend across
history against a goal's target. `reference_date: date` is also
carried, but only `ConsistencyRule` actually reads it. Five independent
rules — `BodyWeightRule` and `BodyFatRule` (fail when the gap to an
active goal's target hasn't narrowed across history, pass when no
active goal or insufficient entries exist), `MeasurementTrendRule`
(surfaces notable changes across nine tape/body-composition fields with
no `Goal` target to fail against — always passes, same precedent as
Goal Alignment's `StrengthGoalRule`), `ConsistencyRule` (the first rule
in the codebase to deliberately *fail*, not pass, on missing or stale
data — grounded in the Bible's Table 54 "Minimum evidence rule"),
`PlateauRule` (flags a trailing run of consecutive entries with no
meaningful body-weight or body-fat movement, approximating the Bible's
"consecutive flat weeks" as consecutive entries since `Progress` has no
weekly cadence — a stated simplification) — see
`docs/adr/0019-progress-evaluation-consistency-and-plateau-scope.md`
for the full reasoning. `ProgressEvaluationRuleEngine` composes all five
by default via the shared `RuleEngine[ProgressEvaluationRuleContext]`.
Produces no training load, exercise recommendation, workout planning,
or AI coaching.

## Training Load Rule Engine

Sprint 3, Phase 8's seventh concrete rule engine
(`app/domain/training_load/rules/`, mirrored by
`tests/domain/training_load/rules/`), the first package whose context
derives nothing at all — `TrainingLoadRuleContext` only sorts and
windows `TrainingLoadSummary` values the application layer already
computed (`TrainingLoad`, a single opaque, non-negative daily scalar),
unlike Progressive Overload's `from_session_contexts()`, which builds
`WorkoutSessionSummary` from raw session data itself.
`trailing_window()` centralizes acute/chronic date-range selection in
one place, anchored to the latest supplied entry's date, never to
`Clock`/today. Five independent rules — `AcuteLoadRule` and
`ChronicLoadRule` (flag a 7-day sum, respectively a 28-day
weekly-equivalent sum, exceeding a configurable ceiling),
`LoadRatioRule` (the acute:chronic workload ratio — "ACWR" in the
sports-science literature — flags a ratio outside a configured
"sweet spot," e.g. Gabbett 2016), `MonotonyRule` and `StrainRule`
(Foster 1998's training monotony `mean/stdev` and strain
`total x monotony`, using population standard deviation, with an
explicit zero-variance special case for both) — see
`docs/adr/0020-training-load-supplied-summaries.md` for the full
reasoning, including why every window size and ceiling is explicitly
literature-grounded rather than Bible-mandated, and how this engine's
rules stay a deliberately independent opinion from Safety's
`WorkloadRule` and Progressive Overload's `VolumeRule`/`DeloadRule`
rather than duplicating either. `TrainingLoadRuleEngine` composes all
five by default via the shared `RuleEngine[TrainingLoadRuleContext]`.
Produces no exercise recommendation, workout planning, or AI coaching.

## Exercise Recommendation Rule Engine

Sprint 3, Phase 9's eighth concrete rule engine
(`app/domain/exercise/rules/`, mirrored by
`tests/domain/exercise/rules/`), the first engine whose evaluation is
scoped to one candidate `Exercise` per call rather than "the user's
current state" — `ExerciseRecommendationRuleContext.exercise` is the
one required field. The first engine to compose other engines'
*already-computed* `RuleResult` outputs (`safety_result`,
`readiness_result`) instead of their raw contexts, so no rule here ever
re-evaluates a check Safety or Readiness already performed — see
`docs/adr/0021-exercise-recommendation-composes-rule-outputs.md` for
the full reasoning. Five independent rules — `ExerciseSelectionRule`
(a soft ADVISORY bias toward `STRENGTH`/`ENDURANCE` goal fit and
current readiness), `ContraindicatedExerciseRule` (the literal Table 48
"Contraindication gate" — fails when the candidate's contraindication
tags overlap a declared restriction, reusing Safety's own
`DeclaredRestriction`, or when `safety_result` is CRITICAL),
`MovementBalanceRule` (a soft ADVISORY push/pull balance bias from a
supplied occurrence tally, Table 48's "Push/pull balance," simplified
from volume to occurrence count), `EquipmentRule` (the literal Table 48
"Equipment mismatch" gate — fails when required equipment is absent
from a supplied availability set), `ProgressionStageRule` (a soft
ADVISORY bias against `ADVANCED`/`INTERMEDIATE` candidates when
Progressive Overload's own session *count* — not its trend
verdicts — is thin). Only `ContraindicatedExerciseRule` and
`EquipmentRule` can fail (Table 48's hard gates); the other three
never fail, expressing their advice purely through `Recommendation`s
attached to a passing result — the existing `RuleResult` shape's own
"passing does not preclude offering advice" capability, no new field
needed. `ExerciseRecommendationRuleEngine` composes all five by default
via the shared `RuleEngine[ExerciseRecommendationRuleContext]`.
Produces no workout generation, scheduling, sets/reps prescriptions, or
AI coaching.

## Application Layer Foundation

Sprint 4, Phase 1 (`app/application/shared/`, mirrored by
`tests/application/`), the framework-independent orchestration
contracts every future use case will depend on — no use case exists
yet. `Command`/`Query` are frozen-dataclass marker base classes (the
same enforcement trick `ValueObject` uses: a subclass forgetting
`frozen=True` fails at class-definition time), each paired with a
`CommandHandler`/`QueryHandler` that both specialize a shared generic
`Handler[TInput, TResult]` (`interfaces.py`). `ApplicationResult[T]` is
a frozen dataclass distinct from the Domain Layer's own `Result`/`Ok`/
`Err` — it expresses a whole workflow's outcome (`success`, `value`,
a tuple of `errors`, a tuple of `warnings`), not one call's binary
split, with `__post_init__` invariant checks raising
`ApplicationResultConstructionError`. `repository.py` re-exports
`app.domain.shared_kernel.repository.Repository` rather than defining
a second interface — `tests/application/shared/test_repository.py`
asserts identity (`Repository is DomainRepository`) to prove it.
`UnitOfWork` is an `ABC` with abstract `commit()`, `rollback()`, and a
generic type-indexed `get_repository(repository_type: type[TRepository])
-> TRepository`; only its context-manager protocol
(`__enter__`/`__exit__`) is concrete — rollback-only-on-exception,
never-suppress, never-auto-commit — the one piece of "universal
coordination glue" this phase treats as legitimately concrete atop an
otherwise-abstract contract. `DomainEventDispatcher` is a one-method
`ABC` (`dispatch(events: Sequence[DomainEvent]) -> None`) responsible
only for *that* dispatch happens, never *when* — always after
`UnitOfWork.commit()`, per `AggregateRoot`'s own "persist first,
publish after" contract. Application-specific exceptions
(`ApplicationError`, `ApplicationResultConstructionError`,
`UnitOfWorkError`, `DomainEventDispatchError`) are a distinct hierarchy
from the Domain Layer's own — see
`docs/adr/0022-application-layer-foundation.md` for the full reasoning.
`tests/application/test_import_boundaries.py` statically enforces that
no file under `app/application/` imports FastAPI, SQLAlchemy, or any
infrastructure module — only `app.domain.*`, `app.application.*`, and
the standard library. No use case, concrete repository, SQLAlchemy,
FastAPI, authentication, REST, or AI integration exists yet.

## Continuous integration

`.github/workflows/ci.yml` runs on every push and pull request: lint, format check,
mypy strict, migration verification and drift detection, the destructive-migration
content check (`scripts/check_destructive_migrations.py`), the Domain Core import-boundary
and 100%-coverage gate, the full pytest suite against a real Postgres service container, a
Docker image build with an import smoke test, and Flutter analyze/test. See the workflow
file itself for why it's structured as independent parallel jobs rather than one long
sequential one, and why there's no Python-version/OS matrix.

## Status

Sprint 1 (Steps 1–12) is complete: the Domain Core skeleton
(`app/domain/shared_kernel/`) is in place — base types only, no product-specific
business logic (see "Domain Core" above).

Sprint 2's aggregates are implemented: `User`, `Workout`, `Exercise`,
`WorkoutSession`, `Progress`, `Nutrition`, `Readiness`, and `Goal` (see
"Domain aggregates" above), domain logic only — no ORM model, repository
implementation, or migration yet for any of them.

Sprint 3, Phase 1 is done: the Rule Engine foundation (see "Rule Engine
foundation" above) — shared architecture only, no fitness-specific rules.

Sprint 3, Phase 2 is done: the Readiness Rule Engine (see "Readiness Rule
Engine" above) — the first of the Bible's nine concrete rule engines.

Sprint 3, Phase 3 is done: the Nutrition Rule Engine (see "Nutrition Rule
Engine" above) — the second.

Sprint 3, Phase 4 is done: the Goal Alignment Rule Engine (see "Goal
Alignment Rule Engine" above) — the first spanning two aggregates (Goal
and Progress).

Sprint 3, Phase 5 is done: the Progressive Overload Rule Engine (see
"Progressive Overload Rule Engine" above) — the first evaluating a
history of snapshots rather than one point in time.

Sprint 3, Phase 6 is done: the Safety Rule Engine (see "Safety Rule
Engine" above) — the first with no aggregate of its own, composing two
other engines' context types instead.

Sprint 3, Phase 7 is done: the Progress Evaluation Rule Engine (see
"Progress Evaluation Rule Engine" above) — the first context to combine
a history of snapshots with a whole referenced snapshot at once, and
the first rule engine with a deliberate exception to the "missing data
passes" convention (`ConsistencyRule`).

Sprint 3, Phase 8 is done: the Training Load Rule Engine (see "Training
Load Rule Engine" above) — the first package whose context derives no
summaries of its own, only sorting and windowing what the application
layer already supplied.

Sprint 3, Phase 9 is done: the Exercise Recommendation Rule Engine (see
"Exercise Recommendation Rule Engine" above) — the first engine scoped
to one candidate per evaluation, and the first to compose other
engines' already-computed `RuleResult` outputs rather than their raw
contexts. Of the Bible's nine named engines, Workout, Recovery
(scoring), Recommendation, Notification, Analytics, and AI Validation
are still ahead.

Sprint 3 is complete: all nine Rule Engines are implemented, tested to
100% domain coverage, and committed.

Sprint 4, Phase 1 is done: the Application Layer Foundation (see
"Application Layer Foundation" above) — the shared orchestration
contracts (`Command`, `Query`, handlers, `ApplicationResult`,
`Repository`, `UnitOfWork`, `DomainEventDispatcher`, application
exceptions) every future use case will depend on. No use case,
concrete repository, SQLAlchemy, FastAPI, or AI integration exists
yet.
