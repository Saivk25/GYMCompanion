# ADR 0031: FastAPI API Layer — thin controllers, dedicated schemas, a stub-container testing strategy, and a `debug=True` bug found by testing the exception handler

- Status: accepted
- Date: 2026-08-05

## Context

The backend was executable without HTTP after the Composition Root
phase (`docs/adr/0030`) — a fully-wired, fully-validated `Container`, 44
Application Layer handlers all resolvable, no live database required to
prove it. Nothing yet exposed any of that over HTTP. The Engineering
Master Plan's Section 3.3 names the API Layer's dependencies as "Domain
Core, Persistence Layer" and this phase's own brief is explicit and
narrow: expose the existing Application Layer through HTTP for five
modules — Workout, Nutrition, Progress, Readiness, Goal — with no
business logic, no repository access, no SQLAlchemy models, and no
authentication (a separate, later phase). User and Exercise are
deliberately not exposed here: `Exercise` has no Application Layer
handlers at all yet, and `User` has handlers but was not named in this
phase's endpoint list.

This phase builds: Pydantic request/response schemas for all five
modules, a generic FastAPI dependency-injection seam over `Container`,
global exception mapping, 37 thin route functions (one per existing
handler), an extended health/liveness/readiness surface, and the
`app/main.py` wiring that ties all of it to `Container`'s lifespan — and,
in the course of actually testing the exception-mapping behavior this
phase's own VERIFICATION section requires, found and fixed a real bug in
how `app/main.py` was about to set FastAPI's `debug` flag (decision 8).

## Decision

1. **Dedicated Pydantic schemas per module (`app/api/schemas/`), never a
   raw Application Layer DTO returned directly from a route.** Every DTO
   in this codebase (`GoalDTO`, `WorkoutDTO`, ...) carries real domain
   value objects (`GoalName`, `WorkoutDate`, ...) as field values —
   returning one directly would require FastAPI to serialize types with
   no defined JSON representation, and would make the API's public
   contract a direct, accidental function of internal domain types free
   to change for domain reasons. A confirmed, exhaustive property made a
   single generic conversion helper viable: every value object across
   all five modules wraps exactly one primitive in a `.value` attribute
   (`str`, `float`, `int`, `date`, or `timedelta` — zero exceptions found
   by inspecting every `value_objects.py` file). `app/api/schemas/
   common.py`'s `unwrap()`/`unwrap_optional()` exploit this once; every
   module's own `from_dto()` classmethod is a mechanical, one-line-per-
   field call site, not hand-written serialization logic repeated five
   times. The one exception to "every value object is a bare primitive
   wrapper" is `ExerciseSet` (`app.domain.workout_session.exercise_set`)
   — a four-field composite (`set_number`, `weight`, `reps`, `rpe`, plus
   a plain `bool`) — so `ExercisePerformanceResponse` unwraps each field
   individually rather than reusing the generic helper.

2. **No range/format validation is duplicated in a request schema.**
   Every such rule — `GoalName` non-empty, `Priority` 1-5, `SleepQuality`
   1-10 — is already enforced exactly once, by the corresponding value
   object's own `__post_init__` (via `ensure()`/`ensure_positive()`,
   `app.domain.shared_kernel.validation`). Re-adding e.g. `Field(ge=1,
   le=5)` to a Pydantic schema would be a second, driftable copy of a
   business rule this phase's own rule ("No business logic") forbids the
   API Layer from owning. A schema's `to_command()` method calls the
   value object constructor directly; if construction raises, that
   exception is `DomainInvariantViolationError` (see decision 4) —
   confirmed, by reading every `value_objects.py` file in full, to be the
   same exception type this codebase already overloads for both
   "structurally impossible internal state" and "the caller supplied an
   out-of-range value," making it the correct signal for the API Layer's
   own global handler to map to 422 rather than 500.

3. **`app/api/deps.py`'s `handler_dependency(handler_type)` is the one
   seam every route uses to resolve a handler — no route calls
   `Container.handler(...)` itself.** `get_container(request: Request) ->
   Container` reads the `Container` FastAPI's lifespan built once at
   process startup, stored on `request.app.state.container`;
   `handler_dependency` wraps that in a small FastAPI dependency that
   calls `container.handler(handler_type)` fresh on every request — the
   same "never cached" design `Container.handler()` itself already
   commits to (ADR 0030, decision 3), inherited here rather than
   reimplemented. This gives every request its own `UnitOfWork` with zero
   extra plumbing per route, and makes "dependency injection everywhere"
   (this phase's own rule) enforceable by one import-boundary test
   (`tests/api/test_import_boundaries.py`) rather than by convention.

4. **`app/api/errors.py` is the one place `ApplicationResult` failures
   and raised exceptions become HTTP responses — routes never construct
   an `HTTPException` themselves except through its three `unwrap_or_*`
   helpers.** `ApplicationResult` (`app.application.shared.
   application_result`) carries no structured error code, only free-text
   `errors`/`warnings` (see that module's own docstring), so the status-
   code mapping is keyed on *which kind of handler produced the failure*,
   confirmed by reading every handler of each kind in this codebase:
   - `unwrap_or_404`: every `GetXHandler`'s only failure mode is "no such
     resource" (its one `ApplicationResult.fail(...)` call site is always
     a `None` lookup result).
   - `unwrap_or_400`: every command handler (create/update/delete/
     transition) fails for a caller-correctable reason.
   - `unwrap_or_500`: every `ListXHandler`'s only failure mode is an
     unexpected exception — there is no caller-correctable "list
     everything" failure.
   Three global exception handlers cover what a route's own `to_command()`
   call or an unexpected failure can raise: `DomainInvariantViolationError`
   -> 422 (see decision 2), `RequestValidationError` (FastAPI/Pydantic's
   own request-shape validation) -> 422, re-wrapped into the same
   envelope, and a bare `Exception` -> 500, logged via `logger.exception`.
   Every failure path — a 400, a 404, a 422 from either source, a 500 —
   produces the exact same `ErrorResponse` shape (`detail: str |
   list[str]`), so a client needs one parser, not four.

5. **Every mutation endpoint (create/update/transition/delete) returns
   `IdResponse` — the affected aggregate's id plus any rule-engine
   warnings — never the full updated resource.** Returning the full
   resource would need a second handler call (fetch-after-mutate) on
   every single mutation route, doubling the handler resolutions (and
   therefore `UnitOfWork`s) per request for no benefit this phase's own
   task list asks for. A caller that wants the updated resource issues
   the corresponding `GET` — one extra round trip, in exchange for every
   mutation route staying exactly one handler resolution, matching "Keep
   controllers extremely small" as literally as this codebase's actual
   handler shapes allow.

6. **API versioning is a URL path prefix, `/api/v1`** — chosen over a
   header-based scheme (`Accept: application/vnd.gym.v1+json`) because
   it's visible in the URL itself, needs no client-side header plumbing,
   and is what every HTTP tool (a browser, `curl`, this project's own
   OpenAPI docs UI) already shows without configuration. `/health`,
   `/health/live`, `/health/ready` stay unversioned and unprefixed —
   liveness/readiness probes are an orchestration concern, not a
   versioned business contract.

7. **`/health/ready` calls `Container.is_database_ready()`
   (`app/composition/container.py`), not `sqlalchemy` directly from
   `app/api`.** A readiness probe's only question — "can this process
   reach its database" — is a pure infrastructure fact with no domain
   meaning, so it's not "business logic in the API layer"; but reaching
   for `sqlalchemy.text()`/`sqlalchemy.exc.SQLAlchemyError` directly
   inside `app/api/routes/health.py` would still put a real SQLAlchemy
   import inside the API Layer, the one thing this phase's "No SQLAlchemy
   models in API" rule most obviously forbids taking literally.
   Delegating the actual connectivity check to a new `Container` method
   keeps every module under `app/api` free of any direct SQLAlchemy
   import — enforced by `tests/api/test_import_boundaries.py`, with no
   per-file exception needed for health.py. `is_database_ready()` never
   raises (catches `SQLAlchemyError` itself, returns `False`) — a health
   endpoint calling it needs a plain boolean, not a driver-specific
   exception vocabulary.

8. **`app/main.py`'s `FastAPI(debug=...)` is always `False` —
   deliberately not `settings.is_local`, which was the first version
   written.** Discovered empirically, not by inspection: Starlette's
   `ServerErrorMiddleware` only calls a registered `Exception` handler
   (`_unhandled_exception_handler`) when `debug=False`; with `debug=True`
   it instead returns an HTML traceback page and still re-raises the
   original exception past the handler entirely (`middleware/errors.py`'s
   own source, confirmed by running `tests/api/routes/test_goal_routes.
   py`'s malformed-id test against the `debug=True` version and watching
   the custom handler get bypassed). This phase's own rule is "global
   exception mapping" — a 500 must come back as the same structured
   `ErrorResponse` envelope everywhere, in local/test the same as
   production — so `debug` cannot track environment the way a bare
   Starlette app's usually does. Nothing is lost for local debugging:
   `_unhandled_exception_handler` still logs the full traceback via
   `logger.exception(...)`, to the process's own log output rather than
   the HTTP response body. This is the highest-value finding of this
   phase's own verification work, the same role ADR 0030's decision 7 bug
   fix played in the prior phase — caught only because exception mapping
   was actually tested end-to-end through a real `TestClient` request,
   not asserted against in isolation.

9. **API Layer tests (`tests/api/`) use two distinct strategies for two
   distinct things worth proving.** Routing/mapping tests (`stub_client`,
   the overwhelming majority) override `app.api.deps.get_container` with
   a fake `Container` that resolves any handler type to a stub always
   returning one fixed `ApplicationResult` — proving "does this route
   convert a result into the right HTTP status and body" with no real
   handler, no real database, no real `UnitOfWork` in the loop; a
   handler's own business logic is `tests/application/`'s job, already
   covered there. Live-lifespan tests (`live_client`/`live_app`) run
   `bootstrap()` for real, against sqlite, for the small number of things
   that only exist once it has — `/health/ready`'s real connectivity
   check, OpenAPI schema generation against the fully-wired app — the
   same "sqlite is sufficient, no live Postgres needed" reasoning ADR
   0030's own tests already establish for composition-level tests. Every
   `stub_client`/`live_client` TestClient is constructed with
   `raise_server_exceptions=False`: Starlette's `ServerErrorMiddleware`
   always re-raises an unhandled exception after sending its response
   ("allows test clients to optionally raise the error within the test
   case" — its own source comment), which would otherwise make a test of
   the 500-mapping path see a raised Python exception instead of the
   actual HTTP response this API's own exception handler produced.

10. **`Container.is_database_ready()` is the one place outside
    `validate()` that `Container` does real I/O — added to
    `app/composition/container.py`, not `app/api/`, in this phase.**
    `Container` already owns `engine`; adding one small method there
    (rather than inventing a second seam) keeps "who owns database
    connectivity checks" answered the same way ADR 0030 already answers
    "who owns the dependency graph." `tests/composition/test_container.py`
    gained two tests for it (reachable/unreachable) alongside this
    phase's own `tests/api/test_health.py` coverage of the HTTP-level
    503 mapping.

## Consequences

**User and Exercise remain unexposed over HTTP**, per this phase's
explicit scope. `User` already has Application Layer handlers
(`app.application.user`) a future, small phase can expose the same way
this one exposed the other five modules; `Exercise` has no Application
Layer handlers at all yet — building `app/api/routes/v1/exercise.py`
would require an Application Layer phase for Exercise first, out of
order with how every other module in this codebase was built.

**Authentication is entirely absent.** Every route in this phase trusts
`user_id` as a plain request field/path parameter with no verification
that the caller *is* that user — acceptable only because this phase's
own directive explicitly defers authentication to a later phase ("Do
not continue to authentication until the API Layer has been reviewed and
accepted") and no route here is reachable outside this development
process yet. The next phase closes this gap; until it does, this API
must not be exposed to any untrusted network.

**No integration test exercises a real Postgres-backed request end to
end** (the same gap ADR 0029 and ADR 0030 already disclosed, still open).
`stub_client` tests prove routing/mapping correctness; `live_client`
tests prove lifespan/health/OpenAPI correctness against sqlite. Neither
proves a `CreateGoalHandler` invocation actually reaching a real
`GoalSqlRepository`'s tenant-scoped Postgres query through a live HTTP
request. Closing this gap needs the same real-Postgres setup ADR 0029
already named (`docker compose up`, point `GYMTEST_DATABASE_URL` at it)
plus `@pytest.mark.integration` API tests this phase does not add.

**Every mutation endpoint's "id + warnings only" response shape
(decision 5) means a frontend that wants to show the updated resource
immediately after a mutation must issue a second `GET`.** A deliberate,
disclosed trade-off, not an oversight — revisit only if a real caller
demonstrates the extra round trip is a genuine problem, not
speculatively now.

**`RuleEngines` (ADR 0030, decision 5) remains unconsumed by any
handler, still.** This phase does not change any handler's constructor
or touch `app/application/` at all — it only resolves existing handlers
through `Container.handler(...)`, exactly the shape ADR 0030 predicted
the API Layer would be the first real consumer of. That prediction is
now true for handler resolution generally; it says nothing new about
`RuleEngines` specifically, which still awaits a handler that asks for
it.
