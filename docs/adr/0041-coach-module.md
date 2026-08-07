# ADR 0041: Coach module — a real, cross-module signal feed, never a chat

- Status: accepted
- Date: 2026-08-07

## Context

Today (ADR 0036), Train (ADR 0037), Fuel (ADR 0038), Progress (ADR 0039),
and Readiness (ADR 0040) established the pattern this phase continues
unchanged: `domain/application/infrastructure/presentation`, a repository
interface behind a Riverpod provider, a disclosed mock implementation,
root-navigator routes for full-screen drill-ins, and honest "not
connected yet" placeholders where a backend capability genuinely does
not exist. This phase applies that pattern to Coach — explicitly framed
by its own build directive as "the application's intelligence layer that
surfaces guidance derived from existing backend capabilities," not a
chatbot, and never permitted to invent intelligence the backend cannot
support.

Research before any screen was built covered every coaching, advisory,
recommendation, rule-engine, and warning capability across the entire
backend (`backend/app/domain/**/rules/`, `app/application/**`,
`app/api/routes/v1/`, `app/api/schemas/`, and every ADR mentioning
recommendation/advisory/rules/coach/readiness/nutrition/workout/
progress):

1. **There is no `coach` concept anywhere in the backend.** A recursive
   search for "coach" across the entire repository (case-insensitive,
   excluding this Flutter client's own pre-existing placeholder) returns
   zero hits. Coach is a pure client-side aggregation concept; nothing
   here reads from a `/coach` endpoint, because no such endpoint, or
   anything like it, exists.
2. **`IdResponse.warnings` is the one, universal, real advisory
   mechanism — and it is transient by construction.**
   `app/api/schemas/common.py`'s `IdResponse` is the response body for
   *every* mutation endpoint (create/update/transition) across Goal,
   Nutrition, Progress, Readiness, and Workout — `{id, warnings}`, where
   `warnings` is `advisory_warnings()` (`app/application/shared/
   advisory_warnings.py`) formatting whichever real `RuleEngine`
   evaluated as part of that exact request. Confirmed by directly
   reading eleven handlers across five modules
   (`record_readiness_handler.py`, `update_sleep_handler.py`,
   `update_recovery_metrics_handler.py`, `record_nutrition_handler.py`,
   `update_nutrition_handler.py`, `update_water_handler.py`,
   `record_progress_handler.py`, `update_body_composition_handler.py`,
   `update_measurements_handler.py`, `complete_workout_session_handler.py`,
   `log_exercise_set_handler.py`, plus Goal's own create/update/complete/
   cancel handlers). **No endpoint anywhere returns this data outside the
   exact mutating call that produced it** — there is no `GET` that
   returns a past recommendation, no aggregation across modules, and
   nothing is persisted server-side beyond the mutation's own primary
   record. A "Coach Home you can open and see fresh guidance on" has, by
   this design, no backing query to call.
3. **Nine rule engines exist; five are genuinely wired to a client-facing
   endpoint, one is dead code from any API consumer's perspective.**
   `ReadinessRuleEngine`, `NutritionRuleEngine`,
   `ProgressEvaluationRuleEngine`, `ProgressiveOverloadRuleEngine` +
   `TrainingLoadRuleEngine` (both invoked together by
   `CompleteWorkoutSessionHandler`), `ExerciseRecommendationRuleEngine`
   (invoked by `LogExerciseSetHandler`, with only a minimal context — see
   that handler's own doc comment on why `goal`/`safety_result`/
   `readiness_result`/`progressive_overload` are all left at their
   documented defaults), and `GoalAlignmentRuleEngine` are all real and
   reachable. **`SafetyRuleEngine` is not.** A direct search
   (`grep -rl SafetyRuleEngine app/application app/api`) returns zero
   hits — it is fully built in the domain layer (ADR 0018), evaluation-
   only by its own design, but no handler anywhere constructs or calls
   it. From a client's point of view it does not exist; Coach does not
   and cannot surface Safety guidance.
4. **`Recommendation` (`app/domain/rules/recommendation.py`) is
   deliberately minimal: a severity and a message, nothing else.** No
   confidence score, no rationale beyond the message, no supporting-data
   payload exists on this type or anywhere in `RuleResult`. Any Coach
   screen showing a "confidence" percentage, an AI-style explanation
   beyond the real message text, or a predictive claim would be
   fabricating data this backend does not produce.
5. **The four subjective-rating/self-report severities
   (`RecommendationSeverity`) are real and exhaustive: `info`,
   `advisory`, `warning`, `critical`.** Nothing between or beyond these
   exists.
6. **No Flutter feature module exists for Goal.** The backend's Goal
   aggregate and `GoalAlignmentRuleEngine` are real and wired, but this
   Flutter app has never built a Goal screen or repository (unlike
   Readiness/Fuel/Progress/Train, all five tabs plus Readiness's own
   module already exist) — there is no user-facing action in this app
   that would ever call a Goal endpoint. Coach cannot surface guidance
   from an action this app has no UI for taking.

This is a narrower, differently-shaped gap than any prior module: it is
not "some dashboards are real, some are placeholders" (Progress) or "one
screen is conditional" (Readiness's Formula) — every *individual*
capability Coach might show is real, but the aggregation, persistence,
and cross-session history the Bible's own named screens assume do not
exist anywhere in the backend's actual design.

## Decision

### 1. Coach is a real, session-scoped feed of real signals — never a chatbot, never a daily brief pulled from a query that doesn't exist

`CoachHomeScreen` replaces the old placeholder `CoachScreen` (previously
describing itself as "Coach conversation," a stale forward-reference
from before this module's real, non-chat build directive existed).
Coach Home shows a chronological feed of real advisory strings, each
one traced directly back to a real `Recommendation` a real rule engine
produced during this app session — never a chat composer, never a typed
message, never a fabricated summary standing in for the daily-brief/
weekly-rollup query research confirmed does not exist.

### 2. A new shared primitive, `CoachSignalLog`, is the only way Coach can have real cross-module content at all

Because no backend query can ever answer "what has the rule engine said
recently across every module" (Decision, research point 2), the only
honest source for that data is capturing it at the moment each
producing module's own controller already receives it from its own real
repository call. `CoachSignal`/`CoachModule`/`CoachSeverity`
(`lib/shared/domain/coach_signal.dart`) and `CoachSignalLog`
(`lib/shared/application/coach_signal_log.dart`) are new, and live in
`lib/shared/`, not `lib/features/coach/`, because Readiness, Fuel, and
Train all *produce* into it — a type four features need cannot live
inside any one of those features' own folders, including Coach's own,
without an unprecedented cross-feature import direction. This is the
first genuinely mutable piece of shared state in this codebase (every
prior shared type was a value type or a stateless widget), and the
first genuinely reactive cross-provider dependency
(`CoachHomeController.build()` uses `ref.listen` +
`ref.invalidateSelf()` to rebuild the moment any producing module pushes
a new signal, rather than requiring a manual pull-to-refresh).
[CoachSignal.parse] never recomputes a severity — it parses the exact
`"[severity] message"` string `advisory_warnings()` already formats, so
a signal's severity on screen is always a direct read of what the real
rule engine classified, never a client-side reinterpretation.

### 3. Readiness, Fuel, and Train are minimally, additively extended to capture warnings their own real backend calls already return

Prior to this phase, only Readiness's own `submitCheckIn` captured and
surfaced its real `warnings` (ADR 0040); Fuel's `logMeal` and Train's
`completeSession` discarded theirs, a scope choice each module's own
prior phase made before Coach existed to consume it. This phase extends
exactly those two call sites — `FuelRepository.logMeal` now returns
`FuelLogResult {entry, warnings}` (mirroring `ReadinessCheckInResult`'s
already-established shape) instead of a bare `FuelEntry`; `TrainSession`
gains a `lastMutationWarnings` field, populated only by
`completeSession`. Both changes are additive and low-risk: `FuelHome
Controller.logMeal`'s prior return value was already discarded
unused, so widening it broke no call site; `TrainSession`'s new field
defaults to `()`, so every existing constructor call across the mock and
its own tests is unaffected. `logWater` and `logSet`/`completeSet` are
deliberately left unchanged — `logWater` maps to the same endpoint but
no nutrition rule is meaningfully about a water-only entry, and
`LogExerciseSetHandler`'s own real context is minimal enough
(Decision, research point 3) that widening every call site for a
realistically-empty case was judged not worth it. Progress's
`logMeasurement` is deliberately **not** extended — see Decision 4.

### 4. Exactly three `CoachModule`s — Recovery, Nutrition, Training — matching the Bible's own three named advice categories, not a fourth for Progress or a fifth for Goal

`ProgressEvaluationRuleEngine`'s real output (body weight/fat trend,
consistency, plateau) does not map cleanly onto Recovery, Nutrition, or
Training, and the Bible names no fourth Coach advice category to place
it in — extending Progress into the signal log would mean inventing a
bucket the Bible itself doesn't ask for. Goal is excluded for the
simpler reason in research point 6: no Flutter UI exists that could ever
produce a Goal-sourced signal. Both are disclosed scope lines, not
oversights.

### 5. The Bible's nine named Coach screens collapse into four real ones

Coach Home (with an `AppSegmentedControl` All/Recovery/Nutrition/
Training filter — satisfying Recommendations, Recovery Advice,
Nutrition Advice, and Training Advice as one real, filtered feed rather
than four separate routes for what is structurally one list), a
Recommendation Detail screen (one signal's full message, severity, and
plain-language sourcing disclosure — genuinely reachable, but
deliberately thin, since a real `Recommendation` carries nothing beyond
severity and message to reveal), Weekly Review, and Coaching History.
The same consolidation discipline ADR 0039 Decision 4 and ADR 0040
Decision 2 already established: a second, differently-named screen
covering the same real data is inventing a screen, not building one the
Bible asks for. "Daily Brief" is not a fifth screen — Coach Home's own
feed, already newest-first and inherently today-weighted in a single
real session, already is the daily brief the Bible describes; a
separate route would just re-show the same list.

### 6. Weekly Review and Coaching History are real, reachable, honest placeholders — not fabricated from session data

Both could technically be *approximated* by counting or grouping
`CoachSignalLog`'s own in-memory entries, but doing so would silently
misrepresent what that data actually is: every signal in the log was
captured this session only, resets on app restart, and is not what a
real week-over-week rollup or a real persisted history would mean. Per
this module's own directive — never fake a capability the backend
cannot support — both render `NotConnectedPlaceholder` directly, naming
exactly what backend capability (a rollup endpoint; a persistence +
query mechanism for past recommendations) doesn't exist, the same
posture every other total gap in this app already takes.

### 7. No confidence score, no rationale beyond the real message, anywhere

The build directive's own design philosophy asks Coach to "prioritize...
confidence" alongside recommendations, explanations, reasoning, and
context. Research point 4 confirms no confidence value exists anywhere
in the backend's `Recommendation`/`RuleResult` types. Rather than
inventing one (a number with no real meaning, or worse, a fabricated
"high/medium/low" label with nothing backing it), every Coach screen
omits confidence entirely and instead leans on the three real,
disclosable things: what the message says, which rule-engine family
produced it (`CoachModule`), and when. `CoachSignalDetailScreen`'s own
"Where this came from" card states this explicitly — real, deterministic
rule output, not a prediction — rather than silently doing nothing where
the Bible's design language expected a confidence signal to appear.

### 8. `AppIcons.coach`/`coachSelected` changed from a chat bubble to `insights_outlined`/`insights`

The prior icon pair (`Icons.chat_bubble_outline`/`chat_bubble`) was
chosen when Coach's own placeholder described itself as "Coach
conversation" — a visual promise this module's real, non-chat build
directive explicitly forbids keeping. Discovered mid-build while wiring
`CoachHomeScreen` into the tab bar, alongside a second, adjacent bug: the
Coach `NavigationDestination` in `lib/shell/app_shell.dart` was the one
of five tab icons using a bare `Icons.chat_bubble_outline` literal
instead of routing through `AppIcons`, the exact "reach directly into
Flutter's full `Icons` class" violation `app_icons.dart`'s own file
doc comment names as the failure mode that icon token file exists to
prevent. Both are fixed together — the icon pair now points at
`insights_outlined`/`insights`, and Coach's own destination now reads
`AppIcons.coach`/`coachSelected`. The other four tabs' own bare `Icons.*`
literals are a separate, pre-existing inconsistency, noted but
deliberately not touched here to keep this change scoped to Coach.

## Consequences

**Coach has no persisted history and no capability that survives an app
restart.** `CoachSignalLog` is in-memory only, exactly like every mock
repository's own state in this codebase, but unlike those, there is no
future "swap for a real HTTP-backed repository" story for the read side
either (`CoachRepository`'s own doc comment states this explicitly) —
only Weekly Review and Coaching History have a plausible future backend
counterpart; Coach Home's live feed's *shape* would stay the same even
with a hypothetical future aggregation endpoint, only its data source
would change.

**Four other modules' own controllers now depend on
`coachSignalLogProvider`.** `ReadinessHomeController.submitCheckIn`,
`FuelHomeController.logMeal`, and `ActiveSessionController
.completeSession` each gained one line pushing real warnings into the
shared log. This is the first cross-feature Riverpod dependency in this
codebase in the "write" direction (a feature module writing into shared
state another feature reads) — disclosed here rather than treated as
routine, since every prior shared promotion (`SessionTier`,
`NotConnectedPlaceholder`) was read-only value/widget reuse, not shared
mutable state.

**`FuelRepository.logMeal`'s return type changed** from `Future<FuelEntry>`
to `Future<FuelLogResult>` — a breaking interface change in principle,
but zero-impact in practice: `FuelHomeController.logMeal`'s prior return
value was already discarded, and no other call site existed.
**`TrainSession` gained a `lastMutationWarnings` field**, additive and
defaulted, affecting no existing call site.

**Ten existing test files needed the same one-line
`coachRepositoryProvider` override added** (`app_shell_test.dart` and
every test that pumps the full `GymCompanionApp`, across Fuel/Progress/
Readiness/Train) — `go_router`'s `StatefulShellRoute.indexedStack`
mounts every branch's widget tree via `IndexedStack` immediately,
including Coach, regardless of which tab is initially active, so any
test booting the app without this override would fail the moment
`coachRepositoryProvider`'s own "throw until overridden" default fires.
This was caught during this phase's own test-writing pass, not
discovered later.

**Still hand-authored, structurally verified — not run in this
sandbox.** Every file in this phase inherits ADR 0002's constraint
unchanged. `coach_signal_flow_test.dart` is the one test in this
codebase that most directly exercises the real cross-module wiring this
ADR describes — submitting a real Readiness check-in and asserting the
exact illustrative string `MockReadinessRepository` returns appears on
Coach Home — and like every other widget test here, has not been run
against a real Flutter SDK.
