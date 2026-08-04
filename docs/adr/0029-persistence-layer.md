# ADR 0029: Persistence Layer — repository/row split, the flush-time sync bridge, tenant-scoping shape, and the unverified-live-RLS gap

- Status: accepted
- Date: 2026-08-05

## Context

Every tenant-scoped aggregate now has an Application Layer (Sprint 4,
`docs/adr/0022`-`0028`), but only one of them — `User` — had ever had a
real persistence implementation, and even that one (`UserAccount` in the
original, single-file `app/infra/models.py`) had drifted out of sync with
`User`'s own Sprint 2 growth (`UserProfile`/`UserPreferences` were never
added to the table). The Engineering Master Plan's Section 3.2
("Persistence Layer") names this module's scope precisely: "One
repository class per aggregate root, hiding SQLAlchemy from every caller
outside infra/" plus "Table definitions, Alembic migrations, RLS policy
definitions, repository implementations," Priority "Must have," Risk
"Medium — an RLS misconfiguration is a cross-tenant data leak."

This phase builds all eight: `User`, `Exercise` (no RLS — global
catalog), `Workout`, `WorkoutSession` (+ `ExercisePerformance`/
`ExerciseSet`), `Progress`, `Nutrition`, `Readiness`, `Goal`. No sandbox
Postgres/Docker/root access was available to build or run any of this
against a real database — see the "unverified" consequence below and
each new migration's own module docstring, which repeats this
constraint at the point a reader would most need it.

Every mutating Application Layer handler already built (e.g.
`UpdateProfileHandler`, `CancelWorkoutHandler`,
`UpdateBodyCompositionHandler`) follows one fixed shape, established
before this phase and out of scope to change: `repository.get(id)`,
mutate the returned aggregate through its own domain methods, then
`uow.commit()` — with no second `repository.add(...)` call. Any
persistence implementation built for this Application Layer has to
support that shape, not a different one this phase would prefer.

## Decision

1. **`app/infra/models.py` (a single file) is replaced by
   `app/infra/models/` (a package), one module per aggregate,
   re-exported from `__init__.py` so `from app.infra.models import X`
   keeps working unchanged for every existing caller (`alembic/env.py`,
   `tests/infra/test_migrations.py`).** Ten mapped classes across eight
   aggregates no longer fit one file the way `UserAccount` alone did.
   `UserAccount` itself is extended in place (`height_cm`, `birth_year`,
   `experience_level`, `biological_sex`, `quiet_hours_starts_at`/
   `quiet_hours_ends_at`, `biometric_app_lock_enabled`,
   `available_equipment`) to catch it up with `User`'s real shape.

2. **`ExercisePerformance`/`ExerciseSet` persist as child tables of
   `workout_sessions` (`exercise_performances`, `exercise_sets`),
   mapped and reconstructed entirely inside
   `WorkoutSessionSqlRepository` — no repository of their own.** This is
   the infra-layer consequence of `docs/adr/0009`'s domain-layer
   decision that these are owned entity/value-object children, not
   separate aggregates. `ExercisePerformanceRow` carries a `sequence`
   integer column with no domain-layer counterpart — SQL rows have no
   inherent order, but `WorkoutSession.exercise_performances` guarantees
   "insertion order == read order" structurally (append-only, never
   reordered); `sequence` is purely how the repository reconstructs that
   guarantee on read, invisible to `app.domain`. `ExerciseSetRow` needs
   no equivalent: `set_number` is already a natural, unique ordering key
   within one performance (enforced by `ExercisePerformance.add_set()`
   rejecting duplicates), so ordering by it recovers the same sequence
   sets were logged in.

3. **A shared `TrackingRepository` base
   (`app/infra/repositories/_tracking.py`) bridges "`get()` returns a
   plain domain aggregate, mutate it, commit, no second `add()` call"
   with SQLAlchemy's flush-based unit of work, via a `before_flush`
   listener registered once per `Session`.** This is the central,
   necessary piece of infrastructure this phase adds beyond
   straightforward column mapping, and the one most worth explaining
   here rather than only in its own module docstring. The problem: the
   abstract `Repository[TAggregate, TId]` contract
   (`app.domain.shared_kernel.repository`) has no `update`/`save`
   method — by design, matching every aggregate's own "load, mutate
   through domain methods, persist" usage pattern already established
   by the Application Layer. A naive repository whose `get()`
   reconstructs a fresh, detached domain object from a row has no way to
   notice that object was mutated afterward; `session.commit()` alone
   would silently write nothing back. `TrackingRepository` closes this
   gap the way *Architecture Patterns with Python* (Percival & Gregory,
   Ch. 2) describes for the identical DDD/SQLAlchemy seam: each
   repository's `get()`/`add()`/`list_by_user()` calls `_track(id,
   aggregate, row)`, pairing the returned aggregate with the
   still-session-attached row it came from; one `before_flush` listener
   per `Session` (idempotent registration, since a unit of work may
   construct several repositories against the same session) then calls
   every tracked repository's `_sync_tracked()`, which re-serializes
   each aggregate's *current* field values onto its row immediately
   before SQLAlchemy writes anything. `session.commit()` then persists
   the up-to-date row exactly as if it had been mutated directly. This
   was evaluated against the alternative of SQLAlchemy's classical
   imperative mapping (mapping domain classes directly onto tables, the
   same book's alternative approach) and rejected: every aggregate here
   has private, underscored fields with no public setters and several
   nested value objects/collections (`UserProfile`, `frozenset[
   EquipmentRequirement]`, `tuple[ExercisePerformance, ...]`), so direct
   attribute instrumentation would need extensive custom `composite()`/
   `properties` wiring per aggregate and would still leave the
   `WorkoutSession` child-table reconciliation problem (decision 5)
   unsolved on its own — more invasive and no less code than the
   row-translation approach this phase already needed regardless.

4. **A concrete `UnitOfWork` (wrapping a `Session` with real
   transactional semantics, and wiring `uow.get_repository(...)` to
   these classes) is explicitly out of scope for this phase — it
   remains exactly as unimplemented as
   `app/application/shared/unit_of_work.py`'s own docstring already
   states.** This phase's repositories are therefore not yet reachable
   from any Application Layer handler in practice; they satisfy their
   abstract `Repository` contracts and are proven against a real,
   migrated schema by `tests/infra/repositories/` (see decision 7), but
   nothing wires `CreateUserHandler` etc. to a `UserSqlRepository` yet.
   That wiring is a Composition Root phase's job, not this one's —
   consistent with `unit_of_work.py`'s own "belongs to whichever future
   phase first implements a use case that needs one."

5. **Tenant scoping is repository-internal wherever the repository
   already has the information to scope safely, and caller-trusted only
   where it structurally cannot.** `add()`/`remove()` receive the
   aggregate itself (which carries its own `user_id` for every
   tenant-scoped aggregate), and `list_by_user(user_id)` receives a
   `user_id` directly — all three call `tenant_scope(session,
   str(user_id))` themselves before touching a row, matching the
   users-table migration's own hard-learned insert-ordering lesson
   ("generate the id, scope the tenant, *then* insert/read"). `get(
   entity_id)` receives only the aggregate's own id, not its owning
   user, so it cannot self-scope without a chicken-and-egg problem
   (reading the row to learn `user_id` requires the scope to already be
   set); every tenant-scoped repository's `get()` therefore trusts the
   caller to have already opened `tenant_scope(session, ...)` on the
   session before calling it — the identical "one `tenant_scope` per
   unit of work, several operations inside it" shape
   `tests/infra/test_migrations.py`'s own cross-tenant test already
   demonstrates. `UserSqlRepository` is the one exception to needing
   caller-trust at all: `users` is the tenant root, so a `User`'s own id
   *is* the tenant boundary, and `get()` there safely scopes from the id
   it was given directly.

6. **Every migration in this phase was hand-written from the
   corresponding `app/infra/models/*.py` module, following the exact RLS
   pattern the users-table migration's own docstring documents, rather
   than produced by `alembic revision --autogenerate`.** No live
   Postgres was reachable in this sandbox (no Docker, no root, no
   `psql`) to run autogenerate against. Each migration's own module
   docstring names this explicitly. As a substitute verification step,
   every migration was checked with `alembic upgrade head --sql` and
   `alembic downgrade head:base --sql` (Alembic's offline mode, which
   needs no live database) to confirm the full nine-migration chain
   executes without a Python or SQL-construction error and produces the
   expected `CREATE TABLE`/`CHECK`/`ENABLE ROW LEVEL SECURITY`/`CREATE
   POLICY` statements in the right order — this proves the migrations
   are *syntactically and structurally* sound, not that the RLS policies
   behave correctly against a real server (see Consequences).

7. **`tests/infra/repositories/` (one file per aggregate) exercises
   every repository's `get`/`add`/`remove`/`list_by_user` against a
   really-migrated schema, plus the flush-time mutation-sync mechanism
   specifically (`test_mutation_persists_without_a_second_add_call` in
   each file) and, for `WorkoutSession`, the multi-table reconciliation
   path (`add_exercise()`/`log_set()`/`remove_exercise()` on a fetched
   session, persisted with no second `add()` call).** All are marked
   `@pytest.mark.integration` and skip cleanly when no Postgres is
   reachable, the same convention `test_migrations.py` already
   established; `tests/infra/conftest.py`'s `migrated_engine` fixture
   (moved there from `test_migrations.py`, which originated it, once
   this phase's tests needed the identical setup) and a new
   `session_factory` fixture built on top of it are what both test
   modules now share. `test_migrations.py` itself gained a parametrized
   `test_every_tenant_scoped_table_has_forced_rls` (structural RLS check
   for all seven new tenant-scoped tables) and
   `test_exercises_table_has_no_row_level_security` (the deliberate
   exception), rather than repeating the full concrete cross-tenant-leak
   scenario eight times — `users`' own
   `test_rls_prevents_cross_tenant_reads` remains the one canonical,
   fully concrete proof every other table's policy is written to match.

8. **`ExerciseSqlRepository` and every method that touches `exercises`
   never call `tenant_scope`.** `Exercise` carries no `user_id` and gets
   no RLS at all (`app/infra/models/exercise.py`'s own module docstring:
   "curated by the system/maintainer... shared/global, not per-user") —
   this is the one repository in the package that is not
   tenant-scoping-shaped at all, not an oversight matching the others.

## Consequences

**None of this has been verified against a live Postgres database in
this session.** The single highest-risk item in the Master Plan's own
risk register for this module ("an RLS misconfiguration is a
cross-tenant data leak") is exactly the property that could not be
exercised here. What *was* verified: every model/repository file passes
Ruff, Ruff format, and mypy --strict with zero errors; the full
nine-migration chain generates valid `upgrade`/`downgrade` SQL in
Alembic's offline mode with no exceptions; every migration's RLS SQL
text was checked by inspection against the users-table migration's
proven pattern. What was **not** verified: that `FORCE ROW LEVEL
SECURITY` actually prevents the app's own connection role from bypassing
a policy on any of the seven new tables (proven, for `users` only, by
the pre-existing `test_rls_prevents_cross_tenant_reads`); that the
insert-then-read-back ordering (`tenant_scope` before insert) actually
avoids the RETURNING-governed-by-USING failure the users migration's
docstring describes, for any table besides `users`; that
`TrackingRepository`'s `before_flush` sync produces correct SQL
`UPDATE`s against a real server, for any repository; and that the
`WorkoutSession` multi-table reconciliation's delete-children-before-
parent ordering satisfies the real foreign-key constraints at commit
time. **Before this phase is trusted in production, a developer with a
real Postgres instance must run:**
`docker compose up` (or an equivalent local Postgres) with
`GYMTEST_DATABASE_URL` pointed at it, then
`pytest tests/infra -m integration`, and confirm every test in
`test_migrations.py` and `tests/infra/repositories/` passes. This
requirement was surfaced to, and explicitly accepted by, the user before
this phase began (two `AskUserQuestion` exchanges: "Persistence Layer —
all aggregates at once" and "single final commit," both made with this
sandbox constraint disclosed up front).

A concrete `UnitOfWork` remains unbuilt (decision 4): these repositories
are exercised directly by `tests/infra/repositories/` but not yet
reachable from any Application Layer handler. The next phase that wires
a Composition Root must construct one `TrackingRepository`-based
repository per aggregate against a single shared `Session`-backed
`UnitOfWork`, matching the exact construction/tenant-scoping shape this
phase's own tests already exercise directly.

`app/infra/repositories/_tracking.py`'s `before_flush` mechanism is now
load-bearing for every future repository this codebase adds — any new
aggregate's repository should subclass `TrackingRepository` rather than
reinventing the identity-map/sync pattern, the same way every
`list_by_user()` extension this codebase has added already follows its
own established sibling shape rather than inventing a new one.
