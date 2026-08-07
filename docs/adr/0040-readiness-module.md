# ADR 0040: Readiness module — records own check-ins, Progress keeps the trend charts

- Status: accepted
- Date: 2026-08-07

## Context

Today (ADR 0036), Train (ADR 0037), Fuel (ADR 0038), and Progress (ADR 0039)
established the pattern this phase continues unchanged: `domain/application/
infrastructure/presentation`, a repository interface behind a Riverpod
provider, a disclosed mock implementation, root-navigator routes for
full-screen drill-ins, and honest "not connected yet" placeholders where a
backend capability genuinely does not exist. This phase applies that pattern
to Readiness — the one module named directly in the build directive rather
than derived solely from the UX/UI Design Bible's own tab list, because
Readiness has never been one of the five bottom tabs (Bible Section 3:
Today/Train/Fuel/Progress/Coach). Its screens are reached from Today's
check-in nudge and from Progress's own Recovery segment.

Research before any screen was built covered the complete backend Readiness
implementation (`backend/app/domain/readiness/`, `domain/readiness/rules/`,
`application/readiness/`, `api/routes/v1/readiness.py`,
`api/schemas/readiness.py`), continuing rather than repeating Progress's own
Decision 3 research into the same aggregate:

1. **Six real, recordable inputs — no more, no less.**
   `RecordReadinessRequest`/`ReadinessResponse` carry exactly
   `sleep_duration_seconds`, `sleep_quality`, `energy_level`, `stress_level`,
   `soreness_level`, `resting_heart_rate`, `heart_rate_variability`, plus
   `notes` and a `source` enum (`manual`/`wearable`/`imported`). Every field
   but the identifiers is optional — `Readiness.record()` requires none of
   them.
2. **The four subjective ratings are bounded 1-10, not 1-5.** Confirmed
   directly from `domain/readiness/value_objects.py`'s
   `_MIN_SUBJECTIVE_RATING = 1` / `_MAX_SUBJECTIVE_RATING = 10` — correcting
   this project's own prior assumption from Progress's phase (ADR 0039's
   Decision 3 wording, "1-5 self-report levels," was wrong; this ADR's own
   research is the source of truth going forward).
3. **`ReadinessRuleEngine` genuinely runs after every mutating call, and its
   output genuinely reaches the client — as advisory text, never a score.**
   `RecordReadinessHandler`/`UpdateSleepHandler`/
   `UpdateRecoveryMetricsHandler` each invoke the five-rule engine
   (`SleepRule`/`EnergyRule`/`StressRule`/`SorenessRule`/`RecoveryRule`)
   after commit and surface its `RuleResult.recommendations` as formatted
   `warnings` strings via the shared `advisory_warnings()` helper
   (`application/shared/advisory_warnings.py`) on `POST /readiness` and both
   `PUT` update routes. This is real, non-fabricated data distinct from a
   numeric score — no endpoint returns a score, a band, or a per-rule
   pass/fail breakdown anywhere.
4. **"Check-in" is not a distinct aggregate.** Same finding ADR 0039 already
   made for Progress: no separate check-in entity exists, no
   `pain_flags`/`GI_symptoms` fields exist anywhere in the domain model —
   the Bible's Section 5.4 "pain/GI snapshot" language names a capability
   this backend does not model.
5. **No wearable sync or import pipeline is wired up.** `ReadinessSource
   .wearable`/`.imported` exist in the enum for API-shape fidelity only;
   every check-in any client can create today is `.manual`.

## Decision

### 1. Readiness owns records; Progress keeps owning trend charts

Progress's own Recovery segment (ADR 0039) already charts real sleep/HRV
trend lines from its own independently-seeded 7-day window. Rather than
building a second set of charts inside this module, Readiness Home stays
deliberately light — today's check-in status, a five-entry recent-check-ins
preview, and access to the full timeline and per-entry detail — while
Progress's Recovery segment gains exactly one new link ("Readiness
check-ins") into this module. Records and trends are a real domain split,
not a screen-count-reduction shortcut: submitting, editing, and reviewing
individual check-ins is Readiness's job; charting them over time remains
Progress's, avoiding two independent implementations of the same line chart.

### 2. Nine Bible-named screens collapse into five real ones

The build directive's own screen list — Readiness Home, Today's Check-in,
Sleep, Energy, Stress, Soreness, Resting Heart Rate, Heart Rate Variability,
Recovery Timeline, Recovery Detail, Recovery History, Check-in Flow,
Formula/Score Explanation — maps to five real screens, not thirteen:

- **Readiness Home** — the hub.
- **Readiness Check-in** — one screen for Today's Check-in, Sleep, Energy,
  Stress, Soreness, Resting Heart Rate, HRV, and Check-in Flow combined.
  The Bible's own Section 5.4 spec already describes a single screen ("The
  five input controls only... under ten seconds"); six separate screens for
  six fields on one `RecordReadinessRequest` would invent navigation the
  Bible never asks for, the same discipline ADR 0039's Decision 4 already
  applied to Progress's own screen list.
- **Readiness Timeline** — Recovery Timeline and Recovery History collapse
  into one chronological list, the same reasoning ADR 0039 Decision 4 gave
  for not inventing a second, differently-named screen showing the same
  data.
- **Readiness Entry Detail** — Recovery Detail: one check-in's full
  recorded values.
- **Readiness Formula** — Formula/Score Explanation, built as a real,
  reachable `NotConnectedPlaceholder` per Decision 3 below.

### 3. Formula/Score Explanation is built, not omitted — as an honest placeholder

The build directive is explicit that this screen exists "only if the
backend exposes it." No score or band is exposed. Per the same posture
every other total gap in this app already takes (Train's Personal Records,
Fuel's Food Search/Supplements, Progress's Workout/Reports segments), the
more consistent, defensible reading is a real, reachable route rendering
`NotConnectedPlaceholder` — never a silently missing menu item, and never a
fabricated number.

### 4. The mock repository demonstrates the real warnings capability without reimplementing the rule engine

`MockReadinessRepository.submitCheckIn` returns two fixed, clearly-labeled
illustrative advisory strings on the very first submission only, and an
empty list on every call after. It does **not** duplicate
`ReadinessRuleEngine`'s five real thresholds (7h minimum sleep, energy
>= 4/10, stress <= 7/10, soreness <= 7/10, resting heart rate <= 70bpm, HRV
>= 40ms) anywhere — not even as a disclosed copy. A disclosed-but-duplicated
threshold set could still silently drift from the real one with no way for
this codebase to notice, which is exactly the "recreate backend business
logic inside Flutter" this module's own directive forbids. The mock instead
proves the real, wired-up UI capability (`ReadinessHomeScreen` genuinely
renders whatever `ReadinessCheckInResult.warnings` a repository returns) with
zero numeric comparison logic anywhere in this client, mock included.

### 5. `AppRatingSlider` is a new, justified design-system extension

The Bible's "numeric steppers preferred over free text for structured
logging" rule (Section 10) applies to a genuinely new case here: a *bounded*
1-10 scale, which no existing component modeled. `AppRatingSlider` wraps a
themed `Slider` (`AppTheme` gained a new `sliderTheme` block — flat,
token-driven, no Material default glow) with a label/value row above it,
used for sleep quality, energy, stress, and soreness; the two free
physiological numbers (resting heart rate, HRV) and sleep hours reuse the
existing `AppTextField` decimal-entry pattern `LogMeasurementScreen` already
established, rather than stretching the slider over an unbounded range.

### 6. Pre-fill from the most recent entry, not a blank form

Bible: "pre-filled to yesterday's values as a low-friction default to adjust
rather than re-enter." `ReadinessCheckInScreen` mutates its controller/field
state directly, once, the first time real data is available during `build()`
— before the widgets reading that state are constructed in the same
synchronous pass, so no frame ever paints the un-prefilled values. This is a
deliberate, documented choice, not a `setState`-avoidance anti-pattern.

### 7. Cross-module wiring: Today's stub becomes real navigation, Progress gains one link

`ReadinessCheckInCard.onStart` (previously `_notBuiltYet(...)`, a stub since
Today's own phase) now pushes `/readiness/check-in` directly — the same
"wire the stub the moment the real screen exists" pattern Train's session
start and Fuel's water log already established for Today. Today's own
`checkInCompletedToday`/`readinessBand` remain `MockTodayRepository`'s own
independently-mocked concepts; submitting a real Readiness check-in does not
retroactively flip Today's header chip, since no backend `RecoveryState`
exists yet to derive a real band from either — a disclosed limitation, not
an oversight. Progress's Recovery segment gains one new `AppListTile`
("Readiness check-ins") between its HRV chart and its own
`NotConnectedPlaceholder`, linking into this module's real check-in
history.

## Consequences

**Readiness has no bottom tab and no tab-root route.** Every route
(`/readiness`, `/readiness/check-in`, `/readiness/timeline`,
`/readiness/entry/:readinessId`, `/readiness/formula`) is a root-navigator
push, reached only from Today's nudge or Progress's Recovery link — a
different navigational shape than every prior module, disclosed in
`app_router.dart`'s own comment block rather than silently treated the same
as Train's/Fuel's/Progress's tab-anchored sub-screens.

**`MockReadinessRepository` is stateful**, like `MockTrainRepository`/
`MockFuelRepository`/`MockProgressRepository` — a submitted check-in must be
visible on the next fetch. It seeds fourteen days of history, deliberately
excluding "today," so the real check-in flow is always immediately
reachable rather than already-completed on first load; reset on every app
restart.

**No score, band, or formula breakdown exists anywhere in this module.**
`ReadinessFormulaScreen` is a real route with a real, honest placeholder —
never a computed number. This is the same disclosed-limitation posture ADR
0037/0038/0039 already established for their own total gaps, applied here
to the one capability this build directive named explicitly as conditional.

**Still hand-authored, structurally verified — not run in this sandbox.**
Every file in this phase inherits ADR 0002's constraint unchanged. Widget
tests locate elements via `find.text`/`find.byType`/
`find.widgetWithText(ElevatedButton, ...)`, the same standard-but-unverified-
here idiom ADR 0037/0038/0039 already disclosed the same risk category for.
`checkin_flow_test.dart`'s timeline-tile-count assertion uses
`findsAtLeastNWidgets` rather than an exact count, since the previous route
(Readiness Home, with its own 5-tile preview) remains mounted underneath a
pushed route rather than being torn down.
