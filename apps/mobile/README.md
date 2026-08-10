# Gym Companion — mobile

The Flutter client: one app, five tabs (Today, Train, Fuel, Progress, Coach), per
`docs/Gym_Companion_UX_UI_Design_Bible.docx` (repository root).

## Layout

- `lib/core/network/` — the shared HTTP layer every real (`ApiX`-prefixed)
  repository is built on: `api_client.dart` (wraps `package:dio`, the one
  place that package is imported outside this folder), `api_config.dart`
  (base URL — platform-aware, see its own doc comment for the Android-
  emulator-vs-`localhost` gotcha — and timeouts), `api_exception.dart` /
  `api_error_mapper.dart` (the one exception type and mapper that ever
  crosses out of this folder, built directly from the real backend's own
  `ErrorResponse{detail}` shape and status-code taxonomy — see
  `backend/app/api/errors.py`), and `interceptors/` (bearer-token
  injection + automatic refresh-then-retry, a GET-only/network-failure-
  only retry policy, and debug-only request logging). Import
  `core/network/network.dart` rather than individual files. See
  `docs/adr/0042-production-integration-plan.md` for the plan this
  implements and `docs/adr/0043-core-networking-layer.md` for this
  layer's own decisions.
- `lib/design/` — the design system: `tokens/` (color, typography, spacing, radius,
  elevation, motion, breakpoints, icons — pure values, no widgets), `theme/`
  (assembles tokens into real `ColorScheme`/`TextTheme`/`ThemeData`), `components/`
  (reusable widget primitives — buttons, cards, badges, list tiles, empty/loading/
  error states, bottom sheet and dialog helpers). Import `design/design.dart` from
  any screen rather than individual token/theme/component files. See
  `docs/adr/0034-flutter-design-system.md` (repository root) for the full reasoning
  behind every token and component choice.
- `lib/shell/` — `app_router.dart` (the `go_router` route table, one `StatefulShellRoute`
  branch per tab, now a `Provider<GoRouter>` rather than a bare top-level constant so it
  can bridge `authControllerProvider`'s state into `go_router`'s `redirect` — see
  `docs/adr/0044-authentication-module.md`) and `app_shell.dart` (the persistent top bar +
  bottom navigation, the Today-only quick-add FAB — see `docs/adr/0036-today-screen.md`
  for why the FAB lives here — and, as of the same phase, real sign-out from the Settings
  icon). Its `AppBar`/`NavigationBar`/`Chip` inherit the design system automatically
  through `ThemeData`'s component themes.
- `lib/core/mapping/` — the shared JSON/DTO/date mapping convention every
  real (`ApiX`-prefixed) repository follows: `json_field.dart` (typed,
  named field extraction off a decoded `Map<String, dynamic>`, failing
  loudly with the field name attached rather than a cryptic type-cast
  error), `api_date_time.dart` (`parseApiDateTime`/`parseApiDate`/
  `apiDateString` — two backend date shapes, two named parsers, never one
  ambiguous `DateTime.parse`). `core/network/`'s sibling, not a layer on
  top of it — network maps transport failures, mapping maps successful
  JSON into DTOs and domain models. See `docs/adr/0045-shared-api-
  mapping-convention.md`.
- `lib/features/auth/` — the real authentication module, the same four-layer
  pattern as every other feature: `domain/` (`AuthState`/`AuthUser`/`AuthTokens`),
  `application/` (`AuthRepository`/`TokenStorage` interfaces + `AuthController`, an
  `AsyncNotifier` handling cold-start refresh, login/register, logout, and the
  refresh/logout closures `ApiClient` calls), `infrastructure/` (`ApiAuthRepository`
  against the real backend, `SecureTokenStorage`, and a test-only `MockAuthRepository`
  never wired in `main.dart`), `presentation/` (Splash, Login, Register). Reached via
  `/splash`/`/login`/`/register`; every other route is guarded by `app_router.dart`'s
  reactive redirect. See `docs/adr/0044-authentication-module.md`.
- `lib/features/<tab>/presentation/` — one screen per tab. `today/`, `train/`,
  `fuel/`, `progress/`, and `coach/` are all real (see below).
  `readiness/` is also real, but is not a tab — see below.
- `lib/features/today/` — the first real feature screen, and the pattern every later
  screen follows: `domain/` (pure Dart view types), `application/` (a `TodayRepository`
  interface + a thin Riverpod `AsyncNotifier`), `infrastructure/` (a disclosed mock
  repository — no real API client yet), `presentation/` (the screen + its widgets).
  See `docs/adr/0036-today-screen.md` for the full reasoning.
- `lib/features/train/` — the same pattern applied to Train: Train Home (This
  Week/History/Library in-page tabs), Pre-session (tier choice), Active Workout
  (set logging + rest timer + session progress, bundled per the UX/UI Design
  Bible's own single-screen spec), Session Summary (shared between a fresh
  completion and viewing a past session), and two honest "not connected yet"
  placeholders (Exercise Detail, Personal Records) where no backend endpoint
  exists at all yet. See `docs/adr/0037-train-module.md`.
- `lib/features/fuel/` — the same pattern applied to Fuel: Fuel Home (today's
  meals, non-alarming hydration progress, weekly-pattern link), Log a meal
  (Photo/Text/Menu capture — Text is the one fully real path; Photo/Menu are
  honest "not connected yet" placeholders, since no vision-AI backend exists at
  all), the water-log bottom sheet (shared with Today's own quick-add), and two
  more honest placeholders (Food Search, Supplements) where no backend concept
  exists yet. See `docs/adr/0038-fuel-module.md`.
- `lib/features/progress/` — the same pattern applied to Progress: Progress
  Home (five in-page-tab dashboards — Workout / Nutrition / Recovery /
  Transformation / Reports — via `AppSegmentedControl`), Log measurements, and
  a measurement's own full trend detail, all real; Photo Check-in, Photo
  Comparison, and Correlations are honest "not connected yet" placeholders,
  since no photo or correlation concept exists in the backend at all; Workout
  and Reports are total placeholder segments, since no analytics or report
  concept exists either. See `docs/adr/0039-progress-module.md`.
- `lib/features/readiness/` — the same pattern applied to Readiness, the one
  module with no bottom tab of its own: Readiness Home (today's check-in
  status, a recent-check-ins preview), Check-in (one screen for sleep,
  energy, stress, soreness, resting heart rate, and HRV — the Bible's own
  single-screen spec), Timeline (every logged check-in, chronological), Entry
  Detail (one check-in's full recorded values), and Formula (an honest "not
  connected yet" placeholder, since no endpoint returns a computed score or
  band). Reached from Today's check-in nudge and from Progress's own Recovery
  segment, never from a bottom tab. Progress's Recovery segment keeps owning
  the sleep/HRV trend *charts*; this module owns check-in records. See
  `docs/adr/0040-readiness-module.md`.
- `lib/features/coach/` — the same pattern applied to Coach, the application's
  intelligence layer, never a chatbot: Coach Home (a real, chronological feed
  of real advisory signals captured from Readiness/Fuel/Train's own genuine
  backend responses, filterable by Recovery/Nutrition/Training via
  `AppSegmentedControl`), Recommendation Detail (one signal's full message,
  severity, and a plain-language "where this came from" disclosure), and two
  honest "not connected yet" placeholders (Weekly Review, Coaching History),
  since no backend rollup or persisted-recommendation-history endpoint exists.
  Reads from the shared `CoachSignalLog` rather than any network-shaped mock
  of its own — there is no aggregation endpoint for a real client to call, so
  unlike every other module's mock, Coach's is not "mock until the backend
  arrives." See `docs/adr/0041-coach-module.md`.
- `lib/shared/domain/` — pure Dart value types genuinely shared across more than
  one feature (`SessionTier`, used by both Today and Train; `CoachSignal`/
  `CoachModule`/`CoachSeverity`, produced by Readiness/Fuel/Train and consumed
  by Coach) — not a dumping ground; a type only moves here once a second
  feature actually needs it, per `docs/adr/0037-train-module.md`'s Decision 5.
- `lib/shared/application/` — cross-feature application state, currently just
  `CoachSignalLog`, a session-scoped, in-memory `Notifier` that Readiness/
  Fuel/Train push real advisory warnings into and Coach reads from — the
  first mutable shared state (and first write-direction cross-feature
  dependency) in this codebase; see `docs/adr/0041-coach-module.md`'s
  Decision 2.
- `lib/shared/presentation/widgets/` — cross-feature widgets that aren't design-
  system primitives, currently `NotConnectedPlaceholder` (promoted from Train
  once Fuel needed the identical "not connected yet" convention a second time —
  `docs/adr/0038-fuel-module.md`'s Decision 5).
- `test/` — mirrors `lib/`, including `test/design/` for the design system and
  `test/features/today/`, `test/features/train/`, `test/features/fuel/`,
  `test/features/progress/`, `test/features/readiness/`,
  `test/features/coach/`, and `test/shared/` for those six modules plus
  shared state.

See `docs/adr/0002-flutter-verification-constraint.md` and
`docs/adr/0003-flutter-state-management.md` for two decisions made during the
scaffolding step that weren't already pinned down by the six planning documents,
and `docs/adr/0034-flutter-design-system.md` for the design system built on top
of that scaffold.

## First-time setup

This project's Dart/Flutter code was authored without a local Flutter SDK available
(see ADR 0002) — **running `flutter pub get` on a real machine is the first real
verification this code gets**, not a formality:

```bash
cd apps/mobile
flutter pub get
flutter analyze
flutter test
flutter run
```

If `flutter pub get` reports a version conflict, that's expected-possible per ADR 0002
— loosen the offending constraint in `pubspec.yaml` and note the fix in a new ADR.

Platform folders (`android/`, `ios/`) are not yet generated — this scaffold is the Dart
application layer only. Generate them with:

```bash
flutter create --platforms=android,ios --org com.gymcompanion .
```

run from inside `apps/mobile/`. This is safe: it only adds the platform folders when
they don't already exist. If it prompts to overwrite `pubspec.yaml`, `lib/main.dart`,
or `test/`, decline (or restore afterward with `git checkout -- pubspec.yaml lib/main.dart test/`)
— those are already hand-written for this project.

## Testing

```bash
flutter test                       # all widget tests
flutter test --coverage            # writes coverage/lcov.info
```

No separate config file is needed beyond `analysis_options.yaml` (Step 6) — Flutter
discovers `test/**/*_test.dart` by convention. `test/shell/app_shell_test.dart` is the
first test: it verifies the app lands on Today and can navigate to Train via the
bottom bar, and that all five tab destinations render. Mirror `lib/`'s folder
structure under `test/` as features are added, matching the backend's `tests/`
convention.

## Formatting

```bash
dart format .            # apply
dart format --output=none --set-exit-if-changed .   # check only, for CI
```

Dart's formatter is deliberately near-unconfigurable (same philosophy as `gofmt` —
one canonical style, no bikeshedding). This project does not override the default
80-column width: newer Dart SDKs support a `formatter: page_width:` key in
`analysis_options.yaml`, but that key needs a newer SDK floor than this project pins
(`>=3.4.0`), and it isn't worth bumping the floor just to gain a setting that hasn't
been verified in this environment (see ADR 0002). Revisit once on a real machine if
the default width genuinely proves cramped in practice — not before.

## Status

All five tabs are real (Today, Train, Fuel, Progress, Coach). Readiness is
also real but is not a tab — it is reached from Today and Progress; see
below. The Flutter Design System (`docs/adr/0034`) is done: tokens, theme architecture
(light + dark), and a closed set of reusable component primitives
(`AppButton`, `AppCard`, `AppBadge`, `AppListTile`, `AppSectionHeader`,
`AppEmptyState`/`AppErrorState`/`AppSkeletonBox`, bottom sheet and confirmation-dialog
helpers) — no `ColorScheme.fromSeed`, no bundled font, no new dependency. `lib/app.dart`
now runs on `AppTheme.light`/`AppTheme.dark` instead of the Step 3 placeholder theme.

An architecture review of that design system was performed and accepted; every
Critical and Important finding it raised has since been resolved (`docs/adr/0035`) —
`AppTheme`/`AppSemanticColors` are memoized, disabled/focus/selection are real named
tokens with a token-driven pressed/hovered/focused interaction system
(`AppOpacity`), touch targets meet 48dp, loading buttons remain screen-reader
accessible, WCAG contrast was computed (not asserted) with two real failures found
and fixed, and typography was audited under large accessibility text sizes across
every named component.

Today (`docs/adr/0036`) is the first real feature screen: readiness band, session
card (loading/ready/completed/empty/error), an outstanding-check-in prompt that
outranks the session card per the UX/UI Design Bible, an understated streak line,
an open-task card, offline indicator, pull-to-refresh, and the Today-only quick-add
FAB. "Start session" navigates for real into Train's Pre-session screen.

As of `docs/adr/0046-today-repository-integration.md` (Step 3 of production
integration, below), `ApiTodayRepository` replaced `MockTodayRepository` as the
real implementation: real workout-plan and check-in-status data from `GET
/api/v1/workouts`/`GET /api/v1/readiness`. The session card's shape changed with
it — `TodaySessionSummary` now shows the workout's real name/goal/notes/planned
date rather than an intensity tier, key-lifts list, duration estimate, or AI
summary, none of which the real `Workout` aggregate models at all. The readiness
band, streak, and open-task card remain disclosed gaps with no backend source
(`docs/TECH_DEBT.md`'s TD-0006) — not this repository's own limitation, the
backend has no Habit/Streak or Task/Recommendation persistence, and no endpoint
returns a computed readiness band. `MockTodayRepository` remains as a test
fixture only.

Train (`docs/adr/0037`) is the second real feature screen, covering every screen
named in its own build directive: Train Home (This Week/History/Library in-page
tabs — the first use of the new `AppSegmentedControl` design-system component),
Pre-session (explicit tier choice, never silently defaulted), Active Workout (set
logging — the first use of the new `AppTextField` component — plus a persistent
rest-timer bar and a session-progress meter, bundled into one screen per the UX/UI
Design Bible's own spec for it), Session Summary (shared between a fresh
completion and viewing a past session from History), and two honest "not
connected yet" placeholder screens (Exercise Detail, Personal Records) where no
backend endpoint exists yet at all — not merely unwired. Built against
`MockTrainRepository`, a stateful mock (unlike Today's) that keeps an in-memory
session so logging a set is actually visible on screen. "Log water" from Today's
own quick-add now opens Fuel's real water-log sheet too.

Fuel (`docs/adr/0038`) is the third real feature screen. Its central finding
reshaped the module more than either of Train's backend gaps: the nutrition
backend has no AI/vision capability anywhere in it (`NutritionSource` is
`manual`/`barcode`/`import` only — no `photo` value at all), so the Bible's
own "Meal Review/Confirm" screen (reviewing an AI reading before it counts)
has no AI reading to review. Capture and Confirm collapse into one real
screen — manual macro entry, the fully working path — with Photo and Menu
capture shown as real, visible options that honestly disclose they aren't
connected yet, using the exact fallback language the Bible itself already
prescribes for a denied camera permission ("text entry remains fully
available... not a degraded fallback"). Food Search and Supplements are two
more honest placeholders. `AppProgressBar` (promoted from Train's local
`SessionProgressBar`) and `NotConnectedPlaceholder` (promoted to
`lib/shared/presentation/`) are both design-system/shared-widget extractions
made the moment a second feature needed them, not guessed at ahead of time.

As of `docs/adr/0049-fuel-repository-integration.md` (Step 3 of
production integration, below), `ApiFuelRepository` replaced
`MockFuelRepository` — real logged-meal and water data from `GET
/api/v1/nutrition`, real logging via `POST /api/v1/nutrition` (the same
endpoint for both meals and water, per the backend's own "one per-entry
log, not a daily rollup" design), and the real, unmodified
`NutritionRuleEngine` warnings that flow into `CoachSignalLog`
unchanged. Unlike Today/Train, no domain-model reduction was needed —
`FuelEntry` already mapped onto `NutritionResponse` field-for-field.
One disclosed gap (`docs/TECH_DEBT.md`'s TD-0008): the weekly
protein-consistency line is always absent, since `ProteinRule` is a
single-entry sanity check, not a personalized weekly target, and no
endpoint returns a computed consistency figure; the existing UI already
guards on this being optional. `MockFuelRepository` remains as a test
fixture only.

Progress (`docs/adr/0039`) is the fourth real feature screen, and the
widest spread of gap severity of any phase so far: Nutrition (a real weekly
protein trend line plus a real weekly consistency heatmap, computed
client-side from real per-entry nutrition totals) and Transformation (real
logged weight/measurements, a real rolling-average chart, a real metric
list) are fully real dashboards; Recovery charts two real raw readiness
inputs (sleep, HRV) alongside one disclosed gap — the composite readiness
score `ReadinessRuleEngine` computes server-side but no endpoint returns;
Workout and Reports are total, disclosed placeholders, since no analytics
or report concept exists in the backend at all. Photo Check-in, Photo
Comparison, and Correlations are real, reachable "not connected yet"
screens rather than silently missing menu items — the same posture Fuel's
Food Search/Supplements and Train's Personal Records/Exercise Library
already established. `AppLineChart` and `AppWeekHeatmap`
(`lib/design/components/`) are this phase's own new chart primitives,
consuming the `chartSeries`/`chartReference` tokens the design system
reserved for exactly this moment rather than guessing at chart needs
ahead of time.

As of `docs/adr/0050-progress-repository-integration.md` (Step 3 of
production integration, below), `ApiProgressRepository` replaced
`MockProgressRepository` — real measurement history from `GET
/api/v1/progress`, real logging via `POST /api/v1/progress` (`unit`/
`source` hardcoded to `'metric'`/`'manual'`, mirroring the mock's own
prior hardcoding, since the backend requires both and no personalized
preference exists anywhere in this client), and real client-side
7-day aggregation over the full `GET /api/v1/nutrition`/`GET
/api/v1/readiness` lists for the Nutrition/Recovery trend charts. This
phase also extended `ProgressRepository.logMeasurement`'s return type
to `ProgressLogResult{entry, warnings}` so the real
`ProgressEvaluationRuleEngine` warnings `POST /api/v1/progress` returns
are no longer silently discarded — unlike Readiness/Fuel/Train, these
render inline on Progress Home's own Transformation segment rather
than flowing into `CoachSignalLog`, since `CoachModule`'s own
deliberately closed three-value enum (`docs/adr/0041`) has no fourth
category for Progress's advisory output. `MockProgressRepository`
remains as a test fixture only.

Readiness (`docs/adr/0040`) is real but has no bottom tab of its own —
reached from Today's check-in nudge and from Progress's own Recovery
segment. Readiness Home, Check-in (one screen for sleep, energy, stress,
soreness, resting heart rate, and HRV, pre-filled from the most recent
entry), Timeline, and Entry Detail are fully real. Real advisory
warnings — genuinely derived server-side by `ReadinessRuleEngine`, never
fabricated client-side — render on Readiness Home when a submission
returns them, and are also pushed into `CoachSignalLog` for Coach Home
to surface. Formula/Score Explanation is a real, reachable "not
connected yet" placeholder, since no endpoint returns a computed
readiness score or band (`docs/TECH_DEBT.md`'s TD-0006); Progress's
Recovery segment keeps owning the sleep/HRV trend charts rather than
this module duplicating them. `AppRatingSlider` (`lib/design/
components/`) is this phase's own new design-system component, for the
bounded 1-10 self-report scale no existing component modeled.

As of `docs/adr/0047-readiness-repository-integration.md` (Step 3 of
production integration, below), `ApiReadinessRepository` replaced
`MockReadinessRepository` — real check-in history from `GET
/api/v1/readiness`, real submissions via `POST /api/v1/readiness`, and
the real, unmodified `ReadinessRuleEngine` warnings that flow through
unchanged, per this phase's own "never duplicate backend business
logic" rule. `MockReadinessRepository` remains as a test fixture only.

As of `docs/adr/0048-train-repository-integration.md` (Step 3 of
production integration, below), `ApiTrainRepository` replaced
`MockTrainRepository` — real workout/session data from `GET
/api/v1/workouts`/`GET /api/v1/workout-sessions/{id}`, real session
start/complete via `POST .../sessions`/`POST .../complete`, mutate →
refetch throughout, and the real, unmodified progressive-overload/
training-load warnings that flow into `CoachSignalLog` unchanged. Three
disclosed gaps, each surfaced and explicitly resolved rather than
defaulted (`docs/TECH_DEBT.md`'s TD-0007): no backend exercise catalog
exists at all, so Active Workout's set logging is deferred —
`logSet`/`completeSet` throw a dedicated exception synchronously,
before any network call, and the screen shows accurate
permanent-unavailability copy instead of misleading "try again" text;
no session-history list endpoint exists, so History is always empty
(the existing empty state already covers it, no UI change needed); and
`tier` has no backend concept, so `TrainWorkout` dropped
`tier`/`estimatedMinutes`/`plannedExerciseNames` entirely (mirroring
Today's own `TodaySessionSummary` reduction), while Pre-session's
`TierPicker` is deliberately kept as a real, inert, client-side-only
control rather than removed. `MockTrainRepository` remains as a test
fixture only.

Coach (`docs/adr/0041`) is the fifth and final tab, and its own research
finding was the widest gap of any phase: the backend has no `coach`
concept at all, and no endpoint anywhere aggregates, persists, or
returns advisory output outside the exact mutating call that produced
it — every rule engine's recommendations are transient by design. Coach
Home is therefore a real, chronological feed built on a new shared
primitive, `CoachSignalLog`, that Readiness's check-in, Fuel's meal log,
and Train's session completion each push their own real, already-
received backend warnings into, filterable by Recovery/Nutrition/
Training via `AppSegmentedControl`. Recommendation Detail shows one
signal's full message, severity, and a plain-language sourcing
disclosure — never a fabricated confidence score or rationale, since the
real `Recommendation` type carries neither. Weekly Review and Coaching
History are honest "not connected yet" placeholders, since no backend
rollup or persisted-recommendation-history concept exists. `SafetyRule
Engine` was found to be fully unwired (zero application-layer callers)
and Goal has no Flutter surface at all, so neither contributes to
Coach. The Coach tab icon changed from a chat bubble to `insights`,
correcting a stale visual promise from before this module's real,
non-chat scope existed.

As of `docs/adr/0051-coach-repository-integration.md` (Step 3 of
production integration, below), Coach's own Step 3 phase is complete
with no `ApiCoachRepository` built and no code changed —
`MockCoachRepository` was already Coach's real implementation before
this phase, and re-verification confirmed the backend still has no
`coach` concept, no aggregation endpoint, and no new rule engine or
Goal surface since ADR 0041's original research. `CoachSignalLog` has
carried genuinely real, backend-sourced warnings (not illustrative mock
text) since Readiness/Fuel/Train each finished their own Step 3 phases,
since the line that populates it reads whichever repository each
module's own provider currently resolves to. `MockCoachRepository`
remains permanently, not as an interim test fixture like the other five
modules' mocks.

Production integration is underway (`docs/adr/0042-production-integration-plan.md`).
Step 1 (`docs/adr/0043-core-networking-layer.md`) built the shared `lib/core/network/`
HTTP layer — `dio`-based client, bearer-token injection, a GET-only/network-failure-only
retry policy, and error mapping built from the real backend's own status-code taxonomy —
with zero feature repositories touched. Step 2 (`docs/adr/0044-authentication-module.md`)
built the real Auth module on top of it: `lib/features/auth/` (Splash/Login/Register),
`AuthController` (cold-start refresh, login, register, logout, automatic refresh-on-401
via `ApiClient`'s closures, logout-on-refresh-failure), `SecureTokenStorage` (refresh
token only, Keychain/Keystore-backed), and a reactive `go_router` guard (`app_router.dart`
is now a `Provider<GoRouter>`) that redirects unauthenticated sessions to `/login` and
authenticated ones away from it. Step 3 (real per-feature repository integration, one feature at a time) is
now complete for all six features: Today (`docs/adr/0046`), Readiness
(`docs/adr/0047`), Train (`docs/adr/0048`), Fuel (`docs/adr/0049`), and
Progress (`docs/adr/0050`) each replaced their mock repository with a
real `ApiXRepository` on the shared mapping convention
(`docs/adr/0045-shared-api-mapping-convention.md`); Coach
(`docs/adr/0051`) closed the same phase without a new repository, since
`MockCoachRepository` already reads real, backend-sourced data via
`CoachSignalLog` — see `MockCoachRepository`'s own doc comment for why
"real API-backed" is not coming, and never needs to, for that one.
