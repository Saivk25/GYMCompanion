# Technical Debt Backlog

Tracks known, deliberately-deferred cleanup in the codebase — duplication
or shortcuts that were evaluated and consciously left as-is, with the
specific condition that would justify revisiting them. This is not a
general TODO list: an item only belongs here if (a) it was identified,
evaluated, and explicitly deferred rather than just forgotten, and (b)
there's a concrete trigger condition for when to act on it, not just "do
it eventually." Each item is numbered; retire (don't delete) an item by
marking it Resolved with the date and the PR/commit that closed it, so
the reasoning stays visible in history.

---

## TD-0001: `_advisory_warnings()` duplicated across 11 handler files

- Status: **Resolved 2026-08-05.** Extracted into
  `app.application.shared.advisory_warnings.advisory_warnings()`. All 11
  call sites updated to import and call the shared function; zero
  behavior or API changes. See "Resolution" below.
- Identified: 2026-08-04, during the post-Phase-5 Application Layer
  consistency review (Workout, Nutrition, Progress).
- Updated: 2026-08-05, Sprint 4 Phase 6 (Readiness) added three more
  call sites, crossing the "9th call site" trigger this item's own
  extraction conditions named. Extraction was deliberately still not
  performed in Phase 6 — that phase's own task was scoped to "maintain
  the current architecture, do not redesign anything," so introducing
  a new shared module mid-phase would itself have violated that
  instruction. See `docs/adr/0027-readiness-application-use-cases.md`'s
  Consequences section for that reasoning at the time.
- Resolved: 2026-08-05, in the standalone refactor between Sprint 4
  Phase 6 and Goal Application Use Cases. See "Resolution" below.

### Current duplication count

The helper

```python
def _advisory_warnings(result: RuleResult) -> tuple[str, ...]:
    return tuple(
        f"[{recommendation.severity.value}] {recommendation.message}"
        for recommendation in result.recommendations
    )
```

is defined byte-for-byte identically in 11 handler files:

- `app/application/nutrition/handlers/record_nutrition_handler.py`
- `app/application/nutrition/handlers/update_nutrition_handler.py`
- `app/application/nutrition/handlers/update_water_handler.py`
- `app/application/workout/handlers/complete_workout_session_handler.py`
- `app/application/workout/handlers/log_exercise_set_handler.py`
- `app/application/progress/handlers/record_progress_handler.py`
- `app/application/progress/handlers/update_body_composition_handler.py`
- `app/application/progress/handlers/update_measurements_handler.py`
- `app/application/readiness/handlers/record_readiness_handler.py`
- `app/application/readiness/handlers/update_sleep_handler.py`
- `app/application/readiness/handlers/update_recovery_metrics_handler.py`

Each was added independently, in four different phases (`docs/adr/0024`,
`docs/adr/0025`, `docs/adr/0026`, `docs/adr/0027`), each justified by
the same "two call sites sharing one three-line function is not yet the
second real need" reasoning `docs/adr/0024` originally gave. That
reasoning was correct each time it was written — the count only reached
11, past this item's own stated 9-call-site trigger, because each
phase's own task scope forbade mid-phase architectural changes, so the
trigger firing during Phase 6 was flagged rather than acted on
immediately (see the "Updated" note above).

### Why extraction is intentionally deferred

The user's own review instruction for this cleanup was explicit: only
extract when it clearly reduces duplication or improves maintainability,
and do not perform speculative abstraction. Deferring here, rather than
extracting immediately, is a deliberate choice for three reasons:

1. **The 8 copies are identical today, but the call sites are not
   symmetric in why they call it.** Nutrition's three handlers evaluate
   a single-entry context; Progress's evaluate a full user history;
   Workout's two evaluate trend-based engines with different
   `RuleResult` shapes feeding in. A shared helper is safe to extract
   now precisely because the formatting logic doesn't yet vary — but
   extracting it while a fourth aggregate (Readiness, Goal) hasn't yet
   supplied its own call site risks guessing at a shape (e.g. severity
   ordering, truncation, locale) that the next 1-2 real call sites might
   immediately need to override, which is exactly the "speculative
   abstraction" this cleanup was told not to do.
2. **Doing the extraction now is a mechanical, low-risk change**
   (find/replace 8 call sites, add one shared module, update 8 sets of
   imports and docstrings) **but it is not free** — it touches every
   package under active review and would be safer to batch with the
   next phase that adds a 9th call site, so the shared helper's contract
   is validated against a genuinely new caller rather than only against
   copies of itself.
3. **No functional or correctness risk exists today.** All 8 copies are
   verified identical (this review confirmed it via direct diff), fully
   covered by each handler's own test suite, and produce no divergent
   behavior. This is pure duplication of a formatting helper, not a
   duplicated business rule — the Application Layer has zero business
   logic in this helper to begin with (it only formats a `RuleResult`
   already produced by the Domain Layer).

**Update (2026-08-05):** Readiness's three new call sites (Phase 6) are
byte-identical to the original 8 — the "guessing at a shape a real
caller might need to override" risk item 1 above named did not
materialize this time; all 11 copies still format `RuleResult` the same
way with no variation. This is evidence *for* extraction being safe
now, not against it. It was still not performed in Phase 6 for a
narrower reason than items 1-3 above: that phase's task explicitly
scoped it to "maintain the current architecture, do not redesign
anything," and adding a new shared module is an architectural change
regardless of how low-risk it is. The next unit of work should treat
extraction as the default unless a concrete reason emerges to keep
deferring — item 1's original justification is now weaker than when it
was written.

### Trigger conditions for extraction

Extract `_advisory_warnings()` into a shared module
(`app.application.shared.advisory_warnings`, or similar) when **any** of
the following becomes true:

1. ~~**A 9th call site is added**~~ — **fired 2026-08-05.** Readiness
   Phase 6 brought the total to 11 real, independent call sites across
   four aggregates, well past the threshold this condition named as
   "enough to validate a shared contract against." This condition is
   satisfied; extraction is no longer blocked on it.
2. **Any one copy needs to diverge from the others** (e.g. a
   severity-based sort, a max-warnings cap, a different message format
   for one aggregate) — if divergence is needed, extract first with a
   parameter for the variation, rather than letting the 11 copies drift
   further apart uncoordinated. Not yet fired: all 11 remain byte-
   identical as of Phase 6.
3. **A bug is ever found in the formatting logic itself** — a single bug
   fixed in only one of 11 copies is worse than the current, verified-
   identical duplication; if a fix is ever needed, that is the moment to
   collapse all 11 into one location so the fix only has to happen once.
   Not yet fired.

**Condition 1 has fired.** The only reason extraction has not yet
happened is that no unit of work has been explicitly scoped to include
it — Phase 6's task explicitly excluded architectural changes. The next
unit of work should either perform the extraction or record a new,
explicit reason for continued deferral; letting this item sit at "Open,
trigger fired" indefinitely defeats the purpose of naming trigger
conditions at all.

### Resolution (2026-08-05)

Extracted as a standalone refactor, scoped explicitly to this item and
nothing else, between Sprint 4 Phase 6 (Readiness) and Goal Application
Use Cases.

- New module: `app/application/shared/advisory_warnings.py`, exposing
  `advisory_warnings(result: RuleResult) -> tuple[str, ...]` —
  byte-for-byte the same logic as all 11 prior copies, re-exported from
  `app.application.shared.__all__` alongside this package's other
  interfaces.
- All 11 call sites listed above updated to import and call the shared
  function; each local `_advisory_warnings()` definition and its
  now-redundant `RuleResult` import removed.
- New tests: `tests/application/shared/test_advisory_warnings.py`
  (4 tests), covering single-recommendation formatting, ordering across
  multiple recommendations, the empty-tuple case, and the return type.
- Zero behavior changes, zero API changes, zero DTO/repository/rule
  engine changes. Full verification gate passed: Ruff, Mypy, full
  backend test suite (1850 passed, 5 skipped — the 5 skips are the
  pre-existing, unrelated "no reachable Postgres" migration tests),
  import boundary tests, and coverage (100%, 0 missing statements/
  branches on `app.domain` + `app.application`; total statement count
  dropped from 5740 to 5723 as the direct, expected effect of collapsing
  11 duplicate function bodies into 1).
- Post-extraction duplication review found no newly-emerged shared
  concept. The `get_repository(X)  # type: ignore[type-abstract]`
  boilerplate (45 occurrences across 38 files) remains a known,
  separately-tracked, lower-priority candidate from the original
  Phase-5 consistency review — it predates this extraction, did not
  change as a result of it, and has no trigger condition of its own
  defined here. No new item was opened for it as part of this
  resolution.

---

## TD-0002: No per-resource ownership authorization on 27 `v1` routes

- Status: **Open.**
- Identified: 2026-08-05, during the Authentication & Authorization
  phase (`docs/adr/0032-authentication-and-authorization.md`).

### What's missing

Every route in `app/api/routes/v1/` (Workout, Nutrition, Progress,
Readiness, Goal) now requires a valid authenticated caller
(`app.api.deps.get_current_user_id`, added this phase). The four
create/list routes per module that used to accept a client-supplied
`user_id` now correctly derive it from the authenticated caller. The
remaining 27 routes — every `GET`/`PATCH`/`PUT`/`DELETE`/action route
addressing one resource by id (`GET /api/v1/goals/{goal_id}`, `DELETE
/api/v1/nutrition/{nutrition_id}`, ...) — require *a* valid
authenticated caller, but do not verify that caller *owns* the
`{resource_id}` named in the path. Any authenticated user can currently
read, update, or delete any other user's goal/workout/progress entry/
etc. by id, provided they know or can guess the id (a UUID — not
trivially guessable, but not a security boundary either).

### Why this was deferred rather than fixed in this phase

This phase's own directive was explicit and scoped: "Secure the
existing API... integrate with the existing architecture... No
shortcuts," but also implicitly bounded by "reuse the existing
UnitOfWork, Container, and dependency injection" and the broader
project convention of one architecturally-scoped change per phase.
Closing this gap requires one of:

1. Each `GetXHandler`/`UpdateXHandler`/`DeleteXHandler`/action handler
   gaining a `caller_id` (or similar) parameter and comparing it against
   the loaded aggregate's own `user_id`, failing with an authorization
   error if they differ — a real signature change to roughly 20+
   already-accepted Application Layer handlers across five modules.
2. Or, the API layer loading the resource first (via a query) to check
   ownership before dispatching the actual command — which would
   violate this phase's own "No repository access from routes" rule and
   double the handler resolutions per mutating request.

Option 1 is the architecturally correct fix, but it touches the
Application Layer signature of every affected handler across five
modules — exactly the kind of cross-cutting redesign this phase's own
scope ("secure the API," not "redesign resource authorization") did not
license doing as a side effect of adding authentication. Implementing
it here, unreviewed, would have been the "shortcut" the phase's own
"No shortcuts" rule warns against in the other direction: rushing a
multi-handler signature change through without its own design pass.

### Trigger conditions for closing this item

1. **The next phase that substantively touches any of Workout,
   Nutrition, Progress, Readiness, or Goal's Application/API layers**
   should close this gap for that module as part of its own scope,
   rather than as an unrelated drive-by change to a phase about
   something else.
2. **Before this API is exposed to any real (non-development) network
   or user base** — this is a real security gap for a multi-tenant
   deployment, not a cosmetic one, and must close before that point
   regardless of whether condition 1 has fired yet.
3. **If a concrete incident or test demonstrates cross-tenant data
   access in practice** — fires immediately, supersedes normal
   phase-scoping.
