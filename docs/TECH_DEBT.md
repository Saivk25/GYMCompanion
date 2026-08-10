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

- Status: **Resolved 2026-08-05.** Every one of the 27 routes now
  verifies `resource.user_id == requester_id` before completing a
  GET/UPDATE/DELETE/ACTION request; a non-owner request now receives
  403 Forbidden instead of succeeding. See "Resolution" below and
  `docs/adr/0033-resource-ownership-authorization.md`.
- Identified: 2026-08-05, during the Authentication & Authorization
  phase (`docs/adr/0032-authentication-and-authorization.md`).
- Resolved: 2026-08-05, in the standalone Resource Ownership
  Authorization phase — exactly trigger condition 1 below, fired by
  the next unit of work that substantively touched all five modules.

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

### Resolution (2026-08-05)

Closed as a standalone phase, scoped explicitly to this item, between
Authentication & Authorization and the start of Flutter work.

- New shared function: `app.application.shared.ownership.ensure_owner(
  *, owner_id: UserId, requester_id: UserId) -> str | None` — the
  single comparison every handler calls, extracted from the first call
  site rather than repeated 27 times (the mistake TD-0001 named and
  this phase deliberately avoided repeating).
- New `forbidden: bool` field and `ApplicationResult.forbid(...)`
  factory (`app/application/shared/application_result.py`) — the one
  bit `app.api.errors._unwrap_or` reads to map any ownership denial to
  403 Forbidden, regardless of which `unwrap_or_*` helper the route
  would otherwise use.
- `requester_id: UserId` added to all 27 addressed-by-id Commands/
  Queries across Goal (4), Workout (3), WorkoutSession (5), Nutrition
  (5), Progress (5), and Readiness (5); every route's previously-unused
  `_user_id` binding is now `user_id`, threaded through as
  `requester_id`. `StartWorkoutSessionHandler` is the one exception —
  it checks the parent `Workout`'s `user_id`, since no `WorkoutSession`
  exists yet at the point the check runs.
- No new layer, base class, decorator, or middleware — authorization
  is an ordinary equality check inside each handler's existing control
  flow. No route function gained any logic; `tests/api/
  test_import_boundaries.py` continues to pass with no new imports in
  `app/api/routes/`.
- New/extended tests: `tests/application/shared/test_ownership.py` (2),
  `tests/application/shared/test_application_result.py` (+5 for
  `forbid()`/the `forbidden`-and-`success` invariant), one
  non-owner-denial test per touched handler (27, including a dedicated
  `StartWorkoutSessionHandler` assertion that no session was added on
  denial), and one API-level end-to-end test
  (`tests/api/routes/test_goal_routes.py`) proving the `forbidden` -> 403
  mapping through a real route, not only at the `ApplicationResult`
  boundary.
- Full verification gate passed: Ruff (check + format), Mypy (`app` +
  `tests`, 0 errors, 761 files), full test suite by directory (Domain
  1,407; Application 626; Infra 23 passed + 51 skipped — no reachable
  Postgres in this sandbox; API 117 passed + 12 skipped; Composition/
  Core 95 — all green), import boundary tests (64 passed), and 100%
  coverage on both new shared modules with no coverage regression on
  any of the 27 touched handlers.
- See `docs/adr/0033-resource-ownership-authorization.md` for the full
  decision record.

---

## TD-0003: `AppShell`'s global top bar bypasses the icon token file and has three dead controls

- Status: **Partially resolved 2026-08-08** (Step 2 of production
  integration — `docs/adr/0044-authentication-module.md`). The
  icon-token bypass (item 1 below) is fully fixed: all five
  `NavigationDestination`s and all four top-bar icons now route through
  `AppIcons`. Of the four dead controls (item 2), Settings is fixed —
  it now opens a real confirmation dialog and calls
  `AuthController.logout()`, exactly the "obvious real destination"
  this item's own trigger condition named. Search and Notifications
  remain open — see the trigger condition below, unchanged.
- Identified: 2026-08-08, during the Production Integration Phase 1
  architecture audit (`docs/adr/0042-production-integration-plan.md`).

### What's wrong

`lib/shell/app_shell.dart` has two separate, related problems:

1. Four of its five `NavigationDestination`s (Today/Train/Fuel/Progress —
   Coach is the exception, fixed in `docs/adr/0041-coach-module.md`) use
   bare `Icons.today_outlined`/`Icons.fitness_center_outlined`/etc.
   literals instead of `AppIcons.today`/`AppIcons.train`/etc., even
   though every one of those tokens already exists in
   `lib/design/tokens/app_icons.dart` — this isn't a missing token, it's
   an existing token going unused at its own intended call site. The top
   bar's `search`/`notifications`/`settings`/`location` icons have the
   identical problem: `AppIcons.search`, `.notifications`, `.settings`,
   and `.location` all already exist and already map to the exact
   glyphs (`Icons.search`, `.notifications_outlined`,
   `.account_circle_outlined`, `.place_outlined`) the bare literals in
   `app_shell.dart` use.
2. Three of the top bar's `IconButton`s (`search`, `notifications`,
   `settings`) have `onPressed: () {}`, and the leading location `Chip`
   has `onDeleted: null` — four interactive-looking controls that do
   nothing when activated. The file's own doc comment discloses this as
   deliberate scaffolding, but every other module's own former
   placeholders have since been converted to real `NotConnectedPlaceholder`
   screens rather than left as no-op taps, and these four never went
   through that pass.

### Why this was not fixed in this audit

The architecture audit phase was explicitly scoped to "review, do not
modify." Fixing the icon-token bypass is a mechanical, low-risk
four-line change; fixing the no-op controls requires a design decision
this phase did not make — where should Search/Notifications/Settings
actually go?

### Trigger conditions for closing this item

1. **The icon-token bypass** should be fixed the next time
   `app_shell.dart` is touched for any reason — pure find-and-replace,
   zero behavior change, no open design question.
2. **The four no-op controls** should be resolved before this app is
   release-candidate quality (Phase 7, Production Polish) — App Store/
   Play Store review will surface a button that visibly does nothing as
   a defect. Settings has an obvious real destination once any account/
   profile screen exists (post-auth); Search and Notifications should at
   minimum become `NotConnectedPlaceholder`s if no real backend concept
   exists by then.

---

## TD-0004: Ad hoc date/duration formatting reimplemented independently in 7+ presentation files

- Status: **Open.**
- Identified: 2026-08-08, during the Production Integration Phase 1
  architecture audit (`docs/adr/0042-production-integration-plan.md`).

### What's duplicated

A private `static String _formattedDate(DateTime date)` (or
`_formattedDateTime`/`_formattedTime`/`_formattedDuration`/
`_formattedElapsed`) is independently defined in at least seven
presentation files: `today_screen.dart`, `train/session_summary_screen.dart`,
`train/widgets/train_history_tile.dart`, `train/widgets/train_workout_card.dart`,
`train/presentation/active_workout_screen.dart`, `readiness/
readiness_entry_detail_screen.dart`, `readiness/widgets/
readiness_entry_tile.dart`, `fuel/widgets/meal_entry_tile.dart`, and
`coach/coach_signal_detail_screen.dart`. Each hardcodes its own literal
month-name array and weekday-indexing logic. Three genuinely different
output formats exist across these copies ("Monday, January 5",
"Jan 5"/"Today"/"Tomorrow", and "January 5, 2026") — some divergence is
a legitimate per-context choice, but seven-plus independent literal
month-name arrays for the same handful of formatting needs is real
duplication.

### Why this was not fixed in this audit

Same reason as TD-0003: audit-only phase. Consolidating into a shared
`lib/shared/presentation/app_date_format.dart` with 3-4 named functions
matching the real output shapes already in use is safe but touches nine
files across five features — a cross-cutting change this project treats
as its own scoped unit of work (see TD-0001's "batch with the next real
caller" precedent), not a drive-by fix.

### Trigger conditions for closing this item

1. **The next feature that needs a tenth independent date-formatting
   helper** — extract at that point rather than write an eighth copy.
2. **Before Phase 6 (Testing) golden tests are written** — consolidate
   first so golden assertions aren't written against output about to be
   refactored.
3. **If any two copies are ever found to disagree on the same output
   shape** — fires immediately.

---

## TD-0005: `TodayScreen`'s quick-add sheet imports Fuel's presentation layer directly

- Status: **Open — accepted, not a defect.**
- Identified: 2026-08-08, during the Production Integration Phase 1
  architecture audit (`docs/adr/0042-production-integration-plan.md`).

### What's coupled

`lib/features/today/presentation/widgets/quick_add_sheet.dart` imports
`../../../fuel/presentation/widgets/water_log_sheet.dart` directly — the
one cross-feature presentation-layer import in the entire Flutter
codebase (confirmed by a full import-direction sweep). Every other
cross-feature reference in the app goes through `lib/shared/`.

### Why this is recorded but not scheduled for a fix

Disclosed, deliberate, from `docs/adr/0037-train-module.md` ("'Log
water' from Today's own quick-add now opens Fuel's real water-log sheet
too") — not new. Recorded as a pattern to watch, not a current problem:
`WaterLogSheet` has no Fuel-internal state dependency beyond
`fuelRepositoryProvider`, already provided at the app root.

### Trigger conditions for revisiting

1. **A second Today -> other-feature presentation import** — two
   independent instances is the signal to promote the shared widget into
   `lib/shared/presentation/widgets/`, the same threshold used everywhere
   else in this project.
2. **If `WaterLogSheet` ever grows a dependency on Fuel-internal state**
   beyond its own repository provider.

---

## TD-0006: No backend source for Today's readiness band, streak, or Task/Recommendation

- Status: **Open.**
- Identified: 2026-08-08, during Step 3 (Today repository integration —
  `docs/adr/0046-today-repository-integration.md`) of `docs/adr/0042-
  production-integration-plan.md`.

### What's missing

`ApiTodayRepository` (`lib/features/today/infrastructure/
api_today_repository.dart`) replaced `MockTodayRepository`, but three of
`TodayViewState`'s fields have no real backend source at all, confirmed
by a full sweep of `backend/app/domain/` and `backend/app/application/`:

1. **`readinessBand`.** `docs/adr/0039-progress-module.md` already found
   this gap for Progress's Recovery segment: `ReadinessRuleEngine`
   computes a composite readiness score/band server-side, but no
   endpoint returns it — only raw per-metric fields (`sleep_quality`,
   `energy_level`, ...) come back from `GET /api/v1/readiness`. This
   phase confirms the same gap applies to Today; `ApiTodayRepository`
   always returns `ReadinessBand.normal`, never computed client-side
   (which would mean re-implementing `ReadinessRuleEngine`'s own scoring
   logic in Flutter).
2. **`streak`.** No Habit/Streak aggregate exists anywhere in
   `backend/app/domain/` or `backend/app/application/` — Domain Model
   Bible Section 4.12's Habit/Streak concept was never built server-side
   at all, not merely un-exposed. `ApiTodayRepository` always returns
   `null` (the field is already nullable; `TodayScreen` already guards
   on it).
3. **`task`.** Same finding for Domain Model Bible Section 4.13's open
   Task/Recommendation concept: `app/domain/rules/recommendation.py` is
   a rule engine's *transient* output type (the same one Coach's own
   `CoachSignalLog` already captures at the moment a mutation produces
   it — `docs/adr/0041-coach-module.md`), not a persisted, independently
   queryable Task aggregate. There is no `GET` endpoint that could ever
   return "the current open task" outside of a mutation response.
   `ApiTodayRepository` always returns `null`.

### Why this was not fixed in this phase

It cannot be fixed from the Flutter side at all — there is no backend
capability to integrate against for any of the three. This phase's own
scope (`docs/adr/0042`) is repository integration against the backend
as it exists today, not backend feature development.

### Trigger conditions for closing this item

1. **A `GET` endpoint is added that returns a computed readiness band**
   (or the raw score `ReadinessRuleEngine` already computes) — closes
   item 1 for both Today and Progress's Recovery segment in the same
   change.
2. **A Habit/Streak aggregate is designed and built server-side** —
   closes item 2. Until then, Today's streak line
   (`_TodayHeader._StreakLine`, `today_screen.dart`) simply never
   renders against real data.
3. **A persisted Task/Recommendation concept is designed and built
   server-side** — closes item 3. Coach's own `CoachSignalLog` remains
   the one real, transient advisory-signal surface until then; it is not
   a substitute for a queryable Task list (see `docs/adr/0041`'s own
   Consequences section for why the two are deliberately not merged).

---

## TD-0007: Train's exercise catalog, session-history, and tier gaps

- Status: **Open.**
- Identified: 2026-08-08, during Step 3 (Train repository integration —
  `docs/adr/0048-train-repository-integration.md`) of `docs/adr/0042-
  production-integration-plan.md`.

### What's missing

`ApiTrainRepository` (`lib/features/train/infrastructure/
api_train_repository.dart`) replaced `MockTrainRepository`, but three
real, disclosed gaps remain — each surfaced explicitly and its handling
approved before implementation, not defaulted silently:

1. **No exercise catalog.** `grep -rli "exercise" backend/app/api` finds
   no `exercise.py` route file at all — there is no endpoint anywhere
   that lists, searches, or resolves an `exercise_id`. `LogExerciseSetHandler`
   (`backend/app/application/workout/handlers/
   log_exercise_set_handler.py`) validates any submitted `exercise_id`
   against the real seeded `Exercise` table and 404s on an unrecognized
   one, so there is no id this client could honestly send for a *new*
   exercise. `ApiTrainRepository.logSet`/`.completeSet` therefore throw
   `TrainLoggingUnavailableException` synchronously, before any network
   call — Active Workout's set-logging UI is real but every attempt to
   use it currently fails with an honest, permanent-unavailability
   message (`active_workout_screen.dart`), not a misleading "try again."
2. **No session-history list endpoint.** `backend/app/api/routes/v1/
   workout.py` has ten endpoints; none of them is `GET
   /workout-sessions` (list) — only `GET /workout-sessions/{id}` (single).
   `TrainHomeViewState.history` is therefore always `[]`;
   `TrainHomeScreen`'s existing `AppEmptyState` for an empty history list
   already renders correctly, so no presentation change was needed.
3. **`tier` has no backend concept.** `StartWorkoutSessionRequest`
   (`backend/app/api/schemas/workout.py`) has exactly one field,
   `session_date` — confirmed the same root cause `docs/adr/0046`
   already found for Today's `tier`/`estimatedMinutes`/
   `plannedExerciseNames`. Unlike those three (removed from `TrainWorkout`
   entirely), the Pre-session screen's `TierPicker` is kept as a real,
   selectable, client-side-only control — `ApiTrainRepository.startSession`
   accepts a `tier` parameter (interface compatibility with
   `TrainRepository`) but never transmits it.

### Why this was not fixed in this phase

Items 1 and 2 cannot be fixed from the Flutter side at all — there is no
backend capability to integrate against for either. Item 3 is a
deliberate choice, not an oversight: removing the tier picker outright
was considered and rejected, since a future backend intensity concept is
plausible and the control costs nothing to keep visible while inert;
this phase's own scope is repository integration against the backend as
it exists today, not a UI-simplification pass.

### Trigger conditions for closing this item

1. **A `GET /exercises`-shaped (or `GET /exercise-catalog`-shaped)
   endpoint is added** — closes item 1: `ApiTrainRepository.logSet`/
   `.completeSet` can then validate/resolve a real `exercise_id` and stop
   throwing `TrainLoggingUnavailableException`.
2. **A `GET /workout-sessions` (list) endpoint is added** — closes item
   2: `ApiTrainRepository.fetchHome` can populate `history` for real.
3. **A `tier`/intensity field is added to `Workout` or
   `StartWorkoutSessionRequest` server-side** — closes item 3:
   `ApiTrainRepository.startSession` can send the real selection instead
   of discarding it.

---

## TD-0008: No backend source for Fuel's weekly protein-consistency label

- Status: **Open.**
- Identified: 2026-08-08, during Step 3 (Fuel repository integration —
  `docs/adr/0049-fuel-repository-integration.md`) of `docs/adr/0042-
  production-integration-plan.md`.

### What's missing

`ApiFuelRepository` (`lib/features/fuel/infrastructure/
api_fuel_repository.dart`) replaced `MockFuelRepository`, but
`FuelHomeViewState.proteinConsistencyLabel` has no real backend source,
confirmed by reading `backend/app/domain/nutrition/rules/protein_rule.py`
directly: `ProteinRule` flags a single logged entry's protein against a
fixed 50-250 g sanity range (its own docstring: "a wide, generic
single-day sanity range... not a personalized macro target"), evaluated
once, at record time, by `RecordNutritionHandler` — never stored, never
aggregated across a week, and no endpoint anywhere returns a computed
"N of the last 7 days on target" figure. `ApiFuelRepository` always
returns `null` (the field is already nullable; `FuelHomeScreen` already
guards on it with `if (state.proteinConsistencyLabel != null)`).

### Why this was not fixed in this phase

It cannot be fixed from the Flutter side at all — there is no backend
capability to integrate against. Computing a "days on target" figure
client-side would require inventing a personalized weekly macro target
this backend does not model anywhere (`ProteinRule`'s own range is
explicitly not one), which would mean fabricating a threshold the real
`NutritionRuleEngine` never computed — exactly the kind of business-
logic duplication this phase's own instructions forbid.

### Trigger conditions for closing this item

1. **A personalized macro-target concept is added to `User`/
   `UserPreferences` server-side, and an endpoint computes a real weekly
   protein-consistency figure from it** — closes this item.
2. **Progress's own Nutrition segment** (`docs/adr/0039-progress-
   module.md`) already renders a real weekly protein trend line computed
   client-side from real per-entry totals, without needing a personalized
   target — if that segment's own approach is ever judged sufficient for
   Fuel's one-line summary too, this could close without a new backend
   endpoint by reusing that same client-side aggregation instead. Not
   done as part of this phase, since it would mean Fuel depending on
   Progress's own computation — a cross-feature coupling decision outside
   this phase's repository-integration scope.

---

## TD-0009: Pull-to-refresh can return a still-cached value instead of guaranteeing a live fetch

- Status: **Open — accepted, disclosed trade-off, not a defect.**
- Identified: 2026-08-10, during Step 4 (offline caching —
  `docs/adr/0052-offline-caching.md`) of `docs/adr/0042-production-
  integration-plan.md`, Decision 7.

### What's accepted

Every `*HomeController.refresh()` (`TodayController`/
`ReadinessHomeController`/`TrainHomeController`/`FuelHomeController`/
`ProgressHomeController`) — used for pull-to-refresh and manual retry —
calls the same `Repository.fetchHome()`/`fetchToday()` that
`readThroughCache` now fronts. A pull-to-refresh within
`kCacheFreshDuration` (5 minutes) of the previous read can return the
still-fresh cached value immediately, with a real background
revalidation kicked off for the *next* read, rather than guaranteeing
that pulling-to-refresh always performs a live network round trip. This
is different from the mutation-invalidation bug this same phase found
and fixed (ADR 0052 Decision 6): pull-to-refresh isn't showing stale
data that masks an action the user just took — it's showing data that
is, at most, `kCacheFreshDuration` old, with a real refresh already in
flight underneath it.

### Why this was not fixed in this phase

Guaranteeing a true bypass-the-cache live fetch on every pull-to-refresh
would require adding a `forceRefresh` parameter to every
`Repository.fetchHome()`/`fetchToday()` signature across all five
repositories — a real interface change this phase's own "keep existing
repository interfaces stable wherever possible" instruction weighs
against, for a UX nicety rather than a correctness bug. `readThroughCache`
already revalidates the cache in the background on every stale-while-
revalidate hit, so the app never runs meaningfully stale for long.

### Trigger conditions for closing this item

1. **User-facing feedback or a design review finds `kCacheFreshDuration`-
   old data on pull-to-refresh confusing or unacceptable** — closes by
   adding an optional `forceRefresh` bool to `readThroughCache` (and
   threading it through each repository's `fetchHome()`/`fetchToday()`
   as an optional, default-`false` parameter — additive, not breaking)
   that skips the freshness check and always calls `fetchRawJson()`.
2. **The next phase that substantively touches `lib/core/cache/`** should
   evaluate this alongside whatever else it's already changing there,
   rather than as an unrelated drive-by fix.
