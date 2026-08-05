# ADR 0033: Resource Ownership Authorization — a shared `ensure_owner()` comparison, a `forbidden` bit on `ApplicationResult`, and `requester_id` threaded into 27 Commands/Queries

- Status: accepted
- Date: 2026-08-05

## Context

ADR 0032 (Authentication & Authorization) closed "is the caller who they
claim to be" but explicitly disclosed, as TD-0002, that it left "is the
caller allowed to touch *this* resource" open: the 27 `GET`/`PATCH`/
`PUT`/`DELETE`/action routes across Goal, Workout (+ WorkoutSession),
Nutrition, Progress, and Readiness required *a* valid authenticated
caller but never compared that caller against the resource's own
`user_id`. Any authenticated user could read, mutate, or delete any
other user's data by id. This phase's brief is exactly TD-0002's own
named trigger condition 1: "the next phase that substantively touches
any of Workout, Nutrition, Progress, Readiness, or Goal's Application/
API layers should close this gap for that module as part of its own
scope."

## Decision

1. **Authorization lives in the Application Layer, inside each
   handler — not in the API layer, and not as a repository-level
   filter.** TD-0002 itself named the two alternatives and rejected
   the API-layer one ("the API layer loading the resource first...
   would violate... No repository access from routes"). A handler
   already loads the aggregate it needs to act on; comparing that
   aggregate's `user_id` against the caller's `requester_id` costs one
   equality check with data already in hand, no extra query, no new
   layer boundary. This keeps `app/api/routes/v1/*.py` exactly as thin
   as ADR 0031 established (build a Command/Query, dispatch it, map
   the result) — no route gained an `if` statement.

2. **The comparison itself is one shared function,
   `app.application.shared.ownership.ensure_owner(*, owner_id, requester_id) -> str | None`,
   not 27 independent copies.** TD-0001's own history — the same
   three-line formatting helper copy-pasted into 11 handlers across
   four phases before being extracted — is the precedent this design
   deliberately did not repeat. `ensure_owner()` was extracted from
   the first handler, not the ninth. It returns `str | None` (a
   denial message, or `None`) rather than a full
   `ApplicationResult[T]`: the generic `T` is not yet known inside a
   shared function with no caller-specific return type, and forcing
   one would require either an unsound cast or an unbound TypeVar at
   every call site. Each handler still writes its own
   `ApplicationResult.forbid([...])` at its own return statement — one
   extra line per handler, in exchange for a shared function whose
   generic signature never fights mypy.

3. **A new `forbidden: bool` field on `ApplicationResult`, not a new
   result type or a structured error code.** ADR 0031 (decision 4)
   already established that `ApplicationResult` carries no structured
   error code — status mapping is keyed by *which kind of handler
   produced the failure*. An ownership denial breaks that pattern: it
   can happen inside a GET-by-id handler, an update handler, or a
   delete handler alike, and always means the same thing regardless of
   which category it occurred in. A single extra bit, checked once in
   `app.api.errors._unwrap_or` ahead of the calling `unwrap_or_*`
   helper's own `failure_status`, maps every ownership denial to 403
   Forbidden with zero per-route or per-`unwrap_or_*` special-casing.
   `ApplicationResult.forbid(errors, *, warnings=())` is the
   fourth factory alongside `ok()`/`fail()`, identical to `fail()`'s
   shape plus `forbidden=True`; `__post_init__` now also rejects
   `forbidden=True` combined with `success=True`, the same
   impossible-state-unrepresentable discipline every other invariant
   on that type already enforces.

4. **`requester_id: UserId` is a new required field on every
   Command/Query that addresses one resource by id** (27 of them:
   4 Goal, 3 Workout, 5 WorkoutSession, 5 Nutrition, 5 Progress, 5
   Readiness — TD-0002's own count, confirmed independently before
   implementation started), threaded from `app.api.deps.
   get_current_user_id` through each route's `body.to_command(...,
   requester_id=user_id)` into the Command/Query, then compared by the
   handler against the loaded aggregate's own `user_id`. Every route
   that previously bound the authenticated caller to an unused
   `_user_id` placeholder (TD-0002's own documented symptom of the
   gap) now binds it to `user_id` and threads it through — the
   underscore's removal is itself evidence the value is finally used.
   `Command`/`Query` are `@dataclass(frozen=True, kw_only=True)`
   marker bases, so adding a new required field to each concrete
   subclass needed no reordering of existing fields.

5. **`StartWorkoutSessionHandler` checks the parent `Workout`'s
   `user_id`, not a `WorkoutSession`'s — the one handler where no
   resource of the type being authorized yet exists.** At the point
   ownership must be verified (before the `_BLOCKED_STATUSES` guard),
   the only aggregate in hand is the `Workout` the new session will
   belong to; a session cannot be checked against its own `user_id`
   before it has been created. Denial rolls back the `UnitOfWork`
   before any session is added — proven by a dedicated test asserting
   `uow.sessions.added == []` on the denial path, not just that the
   result is `forbidden`.

6. **Mutating handlers call `uow.rollback()` explicitly before
   returning `ApplicationResult.forbid(...)`, mirroring the existing
   not-found-handling pattern exactly.** `UnitOfWork.__exit__` only
   auto-rolls-back on an *exception*; an ownership denial is a normal
   return, not an exception, so every mutating handler's denial branch
   rolls back explicitly — the same shape every existing "resource not
   found" branch in these handlers already had, extended by one more
   condition rather than given a new one.

## Consequences

**TD-0002 is closed.** All 27 routes now verify `resource.user_id ==
requester_id` before completing a GET/UPDATE/DELETE/ACTION;
`docs/TECH_DEBT.md` records the resolution alongside its original
scope note and trigger conditions.

**No new abstraction beyond `ensure_owner()` and the `forbidden` bit
was introduced.** No new layer, no new base handler class, no
decorator, no middleware. Authorization is an ordinary equality check
inside a handler's existing control flow — the smallest change that
makes ownership enforcement real without adding a second way to
express "this request failed."

**The API-level 403 mapping was proven end-to-end, not only at the
Application Layer.** `tests/api/routes/test_goal_routes.py` gained one
test stubbing `ApplicationResult.forbid(...)` through a real route and
asserting HTTP 403 — closing a coverage gap on
`app.api.errors._unwrap_or`'s `forbidden` branch that the Application
Layer's own handler-level denial tests could not reach, since those
stop at the `ApplicationResult` boundary and never go through FastAPI's
routing/exception-handling stack.

**No route gained authorization logic of its own.** Every route
function's shape (parse request, build Command/Query with
`requester_id=user_id`, dispatch, unwrap) is identical before and after
this phase — confirmed by `tests/api/test_import_boundaries.py`
continuing to pass with no new imports appearing in `app/api/routes/`.

**Full verification passed:** Ruff (check + format, zero findings
across the full tree), Mypy (`app` + `tests`, 0 errors, 761 files),
the full backend test suite by directory (Domain 1,407; Application
626; Infra 23 passed + 51 skipped — no reachable Postgres in this
sandbox, expected in CI; API 117 passed + 12 skipped; Composition/Core
95 — all green), import boundary tests (Domain, Application, API — 64
passed), 35 dedicated authorization tests (`ensure_owner()`,
`ApplicationResult.forbid()`, and one non-owner-denial test per
touched handler), and 100% coverage on both new modules
(`app.application.shared.ownership`, `app.application.shared.
application_result`) plus no coverage regression on any of the 27
touched handlers (`app.application` remains at 99% overall, with the 6
missed statements confined to pre-existing, unrelated auth-handler
defensive branches this phase did not touch).
