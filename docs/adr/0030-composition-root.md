# ADR 0030: Composition Root — hand-rolled DI, per-resolution `UnitOfWork`/handlers, and a `before_flush`-only sync bug found by finally running it

- Status: accepted
- Date: 2026-08-05

## Context

Every layer through the Persistence Layer (`docs/adr/0022`-`0029`) defines
an abstract seam — `Repository`, `UnitOfWork`, `DomainEventDispatcher`,
`Clock` — and a concrete implementation for most of them, but nothing in
this codebase had ever constructed a full, working object graph from
those pieces. `UnitOfWork` itself was still the abstract interface
`app/application/shared/unit_of_work.py`'s own docstring named
out-of-scope; every handler test built its own ad hoc fakes. The
Engineering Master Plan's Section 3.3 (API Layer) lists its dependencies
as "Domain Core, Persistence Layer" without naming this wiring step
explicitly — this phase is the user-directed precursor that makes that
dependency concrete before any HTTP endpoint exists, per this phase's
own explicit brief: "make the application executable... without
introducing HTTP endpoints yet."

This phase builds: a concrete `UnitOfWork`, a hand-rolled DI container
(`Container`), a concrete `DomainEventDispatcher`, a rule engine
registry, logging configuration, `Settings`-based configuration (already
existing, extended by one field), and `bootstrap()`/`shutdown()`/
`lifespan()` functions — and, in the course of *actually* verifying all
of it (this phase's own explicit instruction: "Actually verify... every
handler can resolve its dependencies... transaction boundaries work"),
found and fixed a real, previously-undetected data-loss bug in the
Persistence Layer's flush-sync mechanism (decision 7).

## Decision

1. **`app/composition/` is a new top-level package — the Composition
   Root — sitting above `app.infra`, importing freely from every layer
   (`app.domain`, `app.application`, `app.infra`, `app.core`).** Not
   `app/bootstrap/`: "Composition Root" is both this phase's own name and
   the standard term (Mark Seemann) for exactly this responsibility — the
   one place allowed to know about every layer at once and wire concrete
   collaborators into the seams each layer already defined for that
   purpose. No import-boundary test constrains it (the existing tests for
   `app.domain`/`app.application` already make the *reverse* direction —
   either of those importing `app.composition` — structurally
   impossible), the same "unconstrained, because it's an outer layer"
   treatment `app.infra` already has.

2. **`SqlAlchemyUnitOfWork` (`app/infra/unit_of_work.py`), not
   `app/composition/`, is where the concrete `UnitOfWork` and the
   repository-type registry (`DEFAULT_REPOSITORY_FACTORIES`) live.**
   Both are Postgres/SQLAlchemy-specific — a `sessionmaker`-backed
   session lifecycle and a `type[Repository] -> concrete class` mapping
   naming eight `app.infra.repositories` classes directly — matching
   `unit_of_work.py`'s own abstract docstring ("A real, Postgres-backed
   implementation... wrapping a SQLAlchemy Session") and the existing
   precedent that every other concrete, storage-aware class already
   lives in `app.infra`, not one layer up. "Repository registration" and
   "UnitOfWork implementation" are therefore one artifact each, not two —
   `Container` composes this registry via `SqlAlchemyUnitOfWork`, it does
   not duplicate it.

3. **Neither `UnitOfWork` nor a handler is ever a long-lived, shared
   singleton — `Container.handler()` constructs a fresh
   `SqlAlchemyUnitOfWork` (and therefore a fresh handler) on every
   resolution.** This is the one architectural rule this phase's whole
   design serves. Every handler already built (frozen, out of scope to
   change) stores `uow` once in `__init__` and re-enters the *same*
   object on every `handle()` call via `with self._uow as uow:`. If
   `Container` cached one handler instance and handed it to two
   concurrent callers (the normal case once an API layer exists), they
   would race on that single object's `self._session` — one request's
   commit could run against another's session. Constructing a fresh
   `SqlAlchemyUnitOfWork` costs nothing (no I/O happens until its own
   `__enter__` opens a session), so this costs nothing to get right. What
   *is* shared, safely, for the container's whole lifetime: `Settings`
   (immutable), the `sessionmaker` itself (thread-safe — only the
   `Session` instances it produces are not), `Clock`
   (`SystemClock` is stateless), the `DomainEventDispatcher`
   (stateless), and every rule engine (pure, stateless — see decision 5).

4. **`Container.handler()` resolves any of this codebase's 44 handlers
   generically, via `inspect.signature`, rather than a hand-maintained
   per-handler registration table.** Every handler already follows
   exactly one of three constructor shapes — `uow` only (13 read-side
   handlers), `uow` + `dispatcher` (7), or `uow` + `dispatcher` + `clock`
   (24) — discovered empirically by inspecting all 44 `__init__`
   signatures before writing this module. A hand-written table naming
   each of the 44 would encode exactly the same information
   `inspect.signature` already recovers from the class itself, with a
   real cost the generic approach doesn't have: **a naive single-line
   grep for handler classes (`class X(CommandHandler`) found only 43 —
   `CompleteWorkoutSessionHandler`'s class statement spans multiple
   lines and was silently missed.** `app/composition/discovery.py`'s
   `discover_handler_types()` (an `ast`-free, `pkgutil.walk_packages` +
   `inspect.getmembers` walk of every module under `app.application`)
   found all 44 correctly — the exact drift risk a hand-maintained list
   carries, demonstrated, not hypothetical. `tests/composition/
   test_dependency_graph.py` parametrizes over this real, 44-item list
   directly, so a 45th handler is included in "every handler resolves"
   coverage automatically, the day it is added, with no second file to
   update.

5. **"Rule engine registration" and "domain service registration" are
   one registry (`RuleEngines`, `app/composition/rule_engines.py`), not
   two.** `app.domain.shared_kernel.service.DomainService`'s own module
   docstring names the nine rule engines as *the* worked example of what
   a "domain service" is in this codebase's vocabulary — registering the
   same eight objects under two different names would be pure
   duplication, which this phase's own standing instruction ("do not
   introduce abstractions because they 'might be useful'") argues
   against exactly as strongly as it does an unneeded interface. All
   eight rule engines this codebase has are constructed once, as shared
   singletons — safe because every one is stateless (`RuleEngine.
   evaluate()` takes its context as a call argument and mutates nothing).
   **This registry is not, today, consumed by any handler.** Every
   handler that already invokes a rule engine (`CreateGoalHandler`,
   `RecordReadinessHandler`, and others) constructs its own private,
   module-level `_rule_engine = SomeRuleEngine()` singleton directly,
   frozen and out of scope for this phase to change. `RuleEngines` exists
   as composition-root-level infrastructure a future caller can obtain
   any of the eight from — `Container.validate()` proves each one
   actually constructs — not as a currently-exercised dependency edge.
   Disclosed here and in the Architecture Delta Review, not hidden.

6. **`LoggingDomainEventDispatcher` (`app/composition/event_dispatcher.
   py`) logs each dispatched event at INFO; it is not a subscriber/pub-
   sub registry.** `app.domain.shared_kernel.events`'s own module
   docstring says this project's event system "stays intentionally
   lightweight for now... not a message broker or an event store" —
   nothing in this codebase has a subscriber yet, so a registry of
   per-event-type callbacks would be exactly the speculative abstraction
   this phase's brief forbids. This dispatcher makes dispatching
   observable (proven in `tests/composition/test_event_dispatcher.py`
   via `caplog`) without inventing anywhere for a subscriber to register
   until one is actually needed. It raises the existing, previously-
   unused `DomainEventDispatchError` if logging an event itself somehow
   raises — unlikely, but keeps that exception meaningful rather than
   permanently dead code.

7. **A real, previously-undetected bug in `TrackingRepository`
   (`app/infra/repositories/_tracking.py`, built in the Persistence
   Layer phase) was found and fixed here: the `before_flush` listener it
   relied on exclusively never fires when nothing in the session is
   already marked new/dirty/deleted — which is exactly the situation
   every "fetch, mutate a plain Python field via a domain method, commit,
   no second `add()`" handler produces, since mutating the domain object
   never touches the underlying SQLAlchemy row directly.** Verified
   empirically against a real (sqlite, for a database-agnostic proof —
   see decision 8) `Session`: `session.commit()` with nothing already
   dirty never fires `before_flush` at all. The result: every mutating
   handler in this codebase — `UpdateProfileHandler`, `CompleteWorkoutHandler`,
   all of them — would have silently lost every mutation-only update
   the moment it ran against a real database, despite `session.commit()`
   returning success. This was invisible in the Persistence Layer phase
   because no live Postgres was reachable there either, so every
   `@pytest.mark.integration` test that would have exercised a real
   commit simply skipped (see ADR 0029's own Consequences section, which
   named this gap explicitly). **Fix**: `_tracking.py` now also
   registers on `before_commit`, which fires unconditionally on every
   `session.commit()` call (also verified empirically) — syncing there
   guarantees the row is current *before* SQLAlchemy decides whether a
   flush has anything to do. `before_flush` stays registered too
   (redundant, harmless — re-syncing already-current values is a no-op),
   covering a hypothetical direct `session.flush()` call with no
   `commit()` around it. This is a bug fix to already-committed,
   otherwise-frozen infra code, made in-scope by this phase's own
   "actually verify... transaction boundaries work" instruction — not a
   refactor for its own sake, and not something a documented Technical
   Debt trigger needed to name in advance, since the trigger *is* the
   demonstrated data-loss bug this phase's own verification work
   surfaced. See the Architecture Delta Review's Critical finding.

8. **`tests/infra/test_unit_of_work.py` proves `SqlAlchemyUnitOfWork`'s
   transactional mechanics (and, incidentally, uncovered decision 7's
   bug) against a minimal, test-only aggregate/row/repository triple on
   sqlite — not against any of the eight real aggregate repositories.**
   Every real repository's `get()`/`add()`/`remove()` calls
   `app.infra.database.tenant_scope`, which executes Postgres's
   `set_config(...)`; sqlite has no such function, and no live Postgres
   is reachable in this sandbox (the same constraint ADR 0029 already
   disclosed). A synthetic `_Widget`/`_WidgetSqlRepository` pair, built
   the same way every real repository already is (subclassing
   `TrackingRepository`), proves `SqlAlchemyUnitOfWork`'s own generic
   commit/rollback/caching behavior — which does not know or care what
   aggregate it is committing — without depending on Postgres-only SQL.
   The eight real repositories' own construction (not their tenant-
   scoped querying, still unverified against a live Postgres — see
   Consequences) is proven separately, and for real, in
   `tests/composition/test_dependency_graph.py`: every one of the eight
   `DEFAULT_REPOSITORY_FACTORIES` entries is constructed against
   `Container`'s real `session_factory` and checked with `isinstance`,
   because — as `SqlAlchemyUnitOfWork`'s own docstring notes —
   constructing a repository does no I/O at all.

9. **`Container.validate()` runs at the end of every `bootstrap()` call
   and needs no live database.** It exercises the entire dependency
   graph this phase is responsible for — all eight repository
   registrations (constructed and `isinstance`-checked), all eight rule
   engines, and all 44 discovered handlers (each resolved and
   `isinstance`-checked) — using nothing but `session_factory()` calls,
   which (per decision 8's own point) never open a connection. A broken
   composition root therefore fails at process startup, synchronously,
   with a specific `CompositionError`, in any environment including one
   with no reachable Postgres — not silently, and not only once a
   request happens to touch the broken part.

10. **`bootstrap()`/`shutdown()`/`lifespan()` (`app/composition/
    bootstrap.py`) are framework-agnostic — no FastAPI import anywhere in
    `app/composition/`.** `lifespan()` is a plain, synchronous
    `@contextmanager`; a future API Layer phase wraps it in a thin async
    FastAPI `lifespan` function rather than reimplementing it, matching
    `app.domain.shared_kernel.repository`'s own stated reason for staying
    synchronous throughout ("the infra layer this will be implemented
    against is already sync"). `app/main.py` is deliberately untouched by
    this phase — wiring `create_app()` to `bootstrap()`/`lifespan()` is
    the API Layer phase's job, per this phase's own explicit rule ("Do
    NOT implement FastAPI routes yet").

11. **No ID generator abstraction is introduced.** The task list named
    this "if planned" — it is not. `EntityId.generate()` (a classmethod
    every aggregate id type already has) already serves this role
    directly inside every handler that mints a new id
    (`UserId.generate()`, `WorkoutId.generate()`, ...), with no injected
    seam requested by any existing design document. Adding one now would
    be exactly the speculative abstraction this phase's brief forbids —
    a swappable strategy with no second implementation and no caller
    that needs one.

## Consequences

**Repository *construction* is now proven; repository *querying* against
a live Postgres — and therefore the tenant-scoping/RLS behavior ADR 0029
already flagged as unverified — still is not.** This phase does not
close that gap; it is orthogonal to what a Composition Root can prove
without a database. The same command ADR 0029 named remains the way to
close it: `docker compose up`, point `GYMTEST_DATABASE_URL` at it, run
`pytest tests/infra -m integration`.

**Decision 7's fix is the highest-value outcome of this phase.** Every
mutation-only handler this codebase has — the majority of the
Application Layer — was silently non-functional against a real database
until this fix, undetected since the Persistence Layer phase because
Postgres was never reachable to prove it either way. This phase's own
"actually verify" instruction is what caught it; a phase that had
treated verification as a formality (running the test suite once, seeing
green because everything skipped) would not have.

**`RuleEngines` (decision 5) and the whole `Container`/handler
constructor-injection mechanism (decision 3-4) are unconsumed by any
handler today.** No handler constructor was changed by this phase (all
are frozen), so nothing yet calls `Container.handler(...)` outside this
phase's own tests. The API Layer phase is expected to be the first real
consumer — each FastAPI route resolving its handler via `Container.
handler(SomeHandler)` per request, exactly the shape `tests/composition/
test_dependency_graph.py` already exercises for all 44.

**`app/main.py`/`app/api/routes/health.py` are unchanged.** A future
readiness endpoint (distinct from the existing liveness-only `/health` —
see that module's own docstring) is a natural, small consumer of
`Container` once the API Layer phase begins, but is explicitly not built
here.
