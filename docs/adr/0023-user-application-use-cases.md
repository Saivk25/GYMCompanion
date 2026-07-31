# ADR 0023: User Application Use Cases — orchestration in handlers, aggregate invocation over business logic, persistence behind interfaces only, and two Domain Layer extensions this phase required

- Status: accepted
- Date: 2026-07-31

## Context

Sprint 4, Phase 2 asked for the first concrete consumer of the
Application Layer Foundation (`docs/adr/0022-application-layer-
foundation.md`): seven command/query handlers coordinating the `User`
aggregate through `UserRepository` and `UnitOfWork`, containing "NO
business rules" of their own, with every decision about what makes a
User valid living on `User` itself. The task named a fixed file list —
five commands (`create_user`, `update_profile`, `update_preferences`,
`update_equipment`, `deactivate_user`), two queries (`get_user`,
`user_exists`), one DTO (`user_dto`), seven handlers — and an ADR
requirement to document why orchestration belongs in handlers, why
handlers invoke aggregates instead of implementing business logic, and
why persistence stays behind repository interfaces.

Two of the five named commands did not map cleanly onto the `User`
aggregate as it stood at the start of this phase:

1. **`update_equipment`** has no corresponding concept on `User` at
   all. The Domain Model & Decision Engine Bible assigns "equipment"
   to `EnvironmentContext` (Section 4.3, Table 6) — a separate,
   not-yet-built aggregate — and `docs/adr/0021-exercise-
   recommendation-composes-rule-outputs.md` had already deliberately
   treated equipment as supplied per-call by the application layer,
   never stored on any aggregate.
2. **`deactivate_user`** names no matching verb on `User`. The
   aggregate's own lifecycle (`app.domain.user.enums.AccountStatus`)
   names `Suspended`, not `Deactivated`.

Given the task's own instruction that "all business behavior must
remain inside the User aggregate," resolving either gap by having a
handler fake the missing behavior (e.g. mutating preferences directly,
or picking a lifecycle transition ad hoc without the aggregate's own
say) would have been exactly the business-logic-in-the-handler outcome
this phase forbids. Both needed a resolved answer before any handler
could be written.

## Decision

1. **Orchestration belongs in handlers because that is the one
   responsibility neither the Domain Layer nor a future Presentation
   Layer can own.** `User.register()`/`update_profile()`/etc. each
   enforce their own invariant in isolation and know nothing about
   *when* they get called, by what, or what happens after
   (`docs/adr/0022-application-layer-foundation.md`, decision 1,
   generalized here to its first real aggregate). A future FastAPI
   route handler's job is translating HTTP to and from application
   concepts, not deciding "load, mutate, commit, dispatch" ordering
   (`docs/adr/0022`, decision 2). Every handler in this package follows
   the identical four-step shape for exactly this reason: `with
   self._uow as uow: repository = uow.get_repository(UserRepository);
   user = repository.get(...); user.<mutate>(...); uow.commit()`, then
   `dispatcher.dispatch(user.pull_domain_events())` *after* the `with`
   block exits successfully — sequencing that belongs nowhere else.

2. **Handlers invoke aggregate methods by name
   (`update_profile`, `update_preferences`, `update_equipment`,
   `suspend`) and never reimplement what those methods decide.** No
   handler in this package contains an `if`/`ensure`/validation of its
   own beyond "does this aggregate exist" (a repository lookup
   outcome, not a business rule) — every field-level or state-machine
   rule (a profile's height bounds, whether a transition is legal from
   the current `AccountStatus`) is already enforced by `User` itself
   before this phase began, or as part of decision 4 below. This is
   the literal mechanism satisfying "no business rules in handlers":
   a handler that only ever calls a named aggregate method has nowhere
   to put a business rule even if someone tried, the same structural
   guarantee `docs/adr/0021`'s composing-outputs-not-inputs pattern
   gives for rule engines.

3. **Every domain-level `DomainInvariantViolationError` is left to
   propagate untouched, in every handler, without exception.** Four
   of the five command handlers (`UpdateProfileHandler`,
   `UpdatePreferencesHandler`, `UpdateEquipmentHandler`,
   `DeactivateUserHandler`) wrap the repository lookup and aggregate
   mutation in a `try`/`except Exception as exc: return
   ApplicationResult.fail([str(exc)])`, but each begins with an
   `except DomainInvariantViolationError: raise` that runs first and
   re-raises unconditionally. `CreateUserHandler` needs no such guard:
   `User.register(...)` is called *before* its `try` even begins, so
   an invariant violation there already propagates without this
   layer's involvement. Both shapes enforce the same rule:
   `app.domain.shared_kernel.errors`' own documented distinction
   between a `DomainError` (an expected, value-carried outcome) and a
   `DomainInvariantViolationError` ("a bug, not a business rule
   failing... there is no meaningful way for a caller to 'handle' a
   broken invariant other than letting it propagate and failing
   loudly") is the Domain Layer's call to make, not this layer's to
   override. Converting an invariant violation into a quietly-returned
   `ApplicationResult.fail(...)` would silently absorb a bug into
   ordinary control flow — exactly what that module's docstring warns
   against. Only genuine repository/`UnitOfWork`-level failures (a
   lost connection, a duplicate-id collision) are the `Exception`s this
   layer's `try` blocks are actually meant to catch.

4. **Persistence stays behind `UserRepository`/`UnitOfWork` because no
   concrete implementation exists yet, by design, and every handler is
   provably indifferent to whatever eventually backs them.** Every
   handler's constructor takes a `UnitOfWork` (`app.application.
   shared.unit_of_work`) and looks up its repository generically via
   `uow.get_repository(UserRepository)` — never a named accessor, never
   an import of `app.infra`, `sqlalchemy`, or `fastapi` (enforced
   statically by `tests/application/test_import_boundaries.py`, which
   this phase adds no exception to). This phase's own tests
   (`tests/application/user/factories.py`) prove the point directly:
   `FakeUserRepository`/`FakeUnitOfWork` are simple in-memory
   dictionaries with no database anywhere in sight, and every handler
   test passes against them unmodified — the concrete, real,
   Postgres-backed implementation a future infrastructure phase writes
   is a drop-in replacement for the fake, not a rewrite of any handler.
   `uow.get_repository(UserRepository)` requires a `# type:
   ignore[type-abstract]` at every call site: mypy's `type-abstract`
   check assumes a `type[T]` argument might be instantiated, but
   `UserRepository` remains abstract in this phase (no concrete
   subclass exists to pass instead) and `get_repository` only ever
   uses the argument as a lookup key, never calls it — a documented,
   narrow false positive, not a typing shortcut.

5. **"Update equipment" is added to `UserPreferences`
   (`app.domain.user.value_objects`) as `available_equipment:
   frozenset[EquipmentRequirement]`, with a matching narrow
   `User.update_equipment(...)` method — a small, explicit Domain
   Layer extension made before this phase's application-layer work
   began.** This is deliberately not the Bible's `EnvironmentContext`
   equipment (a per-session "what's in this specific gym" snapshot);
   it is an account-level "what do I own" default, the same kind of
   fact `quiet_hours`/`biometric_app_lock_enabled` already represent
   on `UserPreferences` — reusing `app.domain.exercise.value_objects.
   EquipmentRequirement` rather than inventing a second equipment type,
   the same "already the right shape" reuse `docs/adr/0021` applied to
   the same type. `UpdateEquipmentCommand`/`UpdateEquipmentHandler`
   remain distinct from `UpdatePreferencesCommand`/
   `UpdatePreferencesHandler` even though both ultimately replace the
   same field, because "update the equipment I own" is a common,
   standalone user action worth its own narrow entry point — the same
   reasoning `User.update_equipment()`'s own docstring gives for why
   the aggregate exposes a matching narrow method rather than forcing
   every equipment edit through a full-preferences replacement.

6. **"Deactivate" maps to `User.suspend()` (Active -> Suspended), not
   `User.delete()`.** The Bible names the lifecycle state `Suspended`,
   never `Deactivated`, leaving the command's own name to interpret.
   Suspension is reversible via the same `User.activate()` that also
   covers Invited -> Active — matching what "deactivate" means in most
   account-management UIs (a temporary, reversible hold), as opposed
   to `delete()`'s permanent, escalation-gated soft deletion. This is
   a naming interpretation, not a new aggregate capability — `suspend()`
   already existed before this phase.

7. **`UserDTO` is a distinct type from `app.domain.user.context.
   UserContext`, not a reuse of it, even though the two overlap in
   most fields.** `UserContext`'s own module docstring scopes it to "a
   future domain service" (a rule engine) and states it will "never be
   persisted or given its own lifecycle" — a domain-internal,
   one-directional snapshot. `UserDTO` answers a different question:
   what a future caller of `GetUserQuery` (eventually, a FastAPI
   response) receives back. The two types exist for different
   consumers with different reasons to change independently; collapsing
   them would couple a future API-versioning concern to a future
   rule-engine-input concern for no benefit — the same reasoning
   `docs/adr/0022` gives for keeping `ApplicationResult` distinct from
   `Result` despite structural overlap.

8. **`UserExistsQuery` is a distinct query from `GetUserQuery`, not a
   thin wrapper around it, because "no such user" means opposite
   things for each.** For `GetUserQuery`, "not found" is the one thing
   that makes the query fail — there is no `UserDTO` to return. For
   `UserExistsQuery`, "not found" is a perfectly successful `False`.
   `UserExistsHandler` never calls `ApplicationResult.fail(...)` for a
   missing user; only a genuine repository-level exception does.
   Forcing both through one query would require one of the two
   handlers to misuse `ApplicationResult.success` against its own
   documented meaning (`docs/adr/0022`'s `ApplicationResult`
   docstring).

9. **"Duplicate user" scenarios are exercised only against
   `CreateUserHandler`, via a repository `add()` failure — not a
   handler-level uniqueness check.** No natural key exists yet to
   check against: `AuthMethod`'s own docstring is explicit that "which
   identity providers exist is an infrastructure/security concern," not
   modeled in this increment, and `UserId` collisions are
   cryptographically improbable by construction (`UserId.generate()`).
   Adding a handler-side "does this already exist" check would invent
   a uniqueness rule the Domain Layer doesn't own — instead,
   `FakeUserRepository(fail_on_add=True)`
   (`tests/application/user/factories.py`) simulates what a real
   unique-constraint violation would surface as, and
   `CreateUserHandler`'s existing repository-failure handling (decision
   4) covers it without any duplicate-specific code path — matching
   the task's own "(where supported by repository contracts)"
   qualifier.

## Consequences

Every handler in this package is now the template a future use case
for another aggregate (Workout, Nutrition, Progress, Readiness, Goal —
all explicitly out of this phase's scope) should follow: load through
`uow.get_repository(SomeRepository)`, mutate by calling a named
aggregate method, commit, pull and dispatch events, catch
`Exception` but never `DomainInvariantViolationError`. Any future
handler that deviates from this shape (e.g. converting an invariant
violation into a failure, or reaching around the aggregate to mutate
its state directly) should be treated as a regression against this
ADR's decisions 2–3, not a stylistic choice.

`UserPreferences.available_equipment` is now real Domain Layer state
with no infrastructure to persist it yet — the same gap this phase
leaves for every field this increment touches (no SQLAlchemy model,
no migration). A future infrastructure phase adding a concrete
`UserRepository` must account for this field alongside every other
`UserPreferences` field it was already going to need to persist. If
`EnvironmentContext` is ever built, a decision will be needed on
whether "available equipment" should be sourced from it, from this
account-level default, or from both (e.g. defaulting to the account
setting, overridable per session) — this ADR does not resolve that
future question, only documents that today's `available_equipment` is
the account-level default, not a session override.

The `# type: ignore[type-abstract]` pattern this phase introduces at
seven call sites will recur at every future handler for every future
aggregate, for the identical reason, until a concrete repository
implementation exists — at which point a future phase could reconsider
whether `get_repository`'s signature can be tightened (e.g. requiring
callers to pass a repository *instance* type bound rather than the
abstract interface) to remove the need for the ignore comment
entirely. This phase does not attempt that change, to stay within its
own explicit scope: contracts and their first concrete consumer, not a
revision of the Application Layer Foundation itself.
