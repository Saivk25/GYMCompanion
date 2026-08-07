# ADR 0039: Progress module — two real dashboards, one partial, two total gaps

- Status: accepted
- Date: 2026-08-07

## Context

Today (ADR 0036), Train (ADR 0037), and Fuel (ADR 0038) established the
pattern this phase continues unchanged: `domain/application/
infrastructure/presentation`, a repository interface behind a Riverpod
provider, a disclosed mock implementation, root-navigator routes for
full-screen drill-ins, and honest "not connected yet" placeholders where
a backend capability genuinely does not exist. This phase applies that
pattern to Progress — the UX/UI Design Bible's "segmented sub-navigation
across Workout / Nutrition / Recovery / Transformation / Reports
dashboards, plus the photo and measurement timeline" (Section 3).

Research before any screen was built covered every one of those five
dashboards against the real backend (`backend/app/domain/progress/`,
`domain/readiness/`, `domain/workout/`, `domain/training_load/`,
`api/routes/v1/`, `api/schemas/`):

1. **Workout trends/analytics — does not exist.** `domain/workout/rules/`
   and `domain/training_load/rules/` compute single-session or
   caller-supplied-summary checks, not trend aggregation, and expose no
   query. No muscle-group, PPL-balance, weekly-volume, PR-trend, or
   adherence-heatmap concept exists anywhere in `domain/workout/` or
   `api/routes/v1/workout.py`.
2. **Nutrition trends — no dedicated endpoint, but real per-entry data
   exists.** `application/nutrition/queries/list_nutrition.py` returns
   raw per-entry `NutritionDTO`s only (ADR 0011, backend: per-entry log,
   not a daily rollup) — the same real data `FuelEntry` is already built
   from.
3. **Recovery/readiness — raw inputs are real; the composite score is
   not exposed.** `ReadinessRuleEngine` (`domain/readiness/rules/`)
   computes a real 5-rule "visible formula" score, but
   `api/schemas/readiness.py`'s `ReadinessResponse` returns only raw
   fields (`sleep_duration_seconds`, `energy_level`, `stress_level`,
   `soreness_level`, `resting_heart_rate`, `heart_rate_variability`) —
   no score, no per-rule breakdown, on any endpoint.
4. **Transformation — measurements and body composition are real;
   photos do not exist at all.** `Progress`'s domain entity
   (`domain/progress/progress.py`) carries real fields for `body_weight,
   body_fat_percentage, lean_body_mass, muscle_mass, waist, chest, hip,
   arm, thigh, calf, neck`, with real CRUD routes
   (`POST/GET/PUT/DELETE /api/v1/progress`). A grep for photo/image/
   picture across the entire backend returns zero real hits — the only
   mention is a doc-comment in `progress.py` naming the Bible's
   `PhotoCheckin` as an explicitly out-of-scope sibling concept.
5. **Reports — does not exist.** A grep for "report" as a noun across
   the whole backend returns zero hits beyond the English verb. No
   generation, listing, detail, or export concept exists anywhere.
6. **Insight/correlation detail — does not exist.** `domain/progress/
   rules/measurement_trend_rule.py` is a threshold-based trend detector,
   not a correlation engine, and explicitly disclaims statistical slope
   computation as "the Statistical layer's job, out of scope here." No
   cross-domain correlation logic exists anywhere in the domain layer.
7. **Check-in as a distinct concept — does not exist.** "Check-in" is
   docstring vocabulary for `Readiness.record()`/`Progress.record()`,
   not a separate aggregate — there is no distinct photo-check-in or
   measurement-check-in command separate from ordinary
   `RecordProgressCommand`.

This is a wider spread than Fuel's single central gap (no AI vision):
Progress has two dashboards with real, complete data (Transformation's
measurements, Nutrition's per-entry totals), one with real inputs but a
missing computed output (Recovery's score), and two with no backend
concept at all (Workout, Reports), plus two named catalog screens
(Photo Comparison, Insight/correlation detail) with no data to show.

## Decision

### 1. Progress Home is one screen with five in-page tabs, not five routes

`AppSegmentedControl` (built during Train's phase, doc-commented at the
time as anticipating "Progress's five dashboards... the largest case the
Bible names") is used exactly as anticipated — Workout / Nutrition /
Recovery / Transformation / Reports as five segments on one
`ProgressHomeScreen`, the same in-page-tab pattern Train's This Week /
History / Library already established, not five separate tab-root
screens.

### 2. Nutrition and Transformation are real dashboards, not placeholders

Both are built from real backend-shaped data:

- **Nutrition** charts a real weekly protein trend and a real weekly
  consistency heatmap, computed client-side from real per-entry
  nutrition totals (`NutritionDayTotal`) — the same legitimate
  client-side summation `FuelHomeViewState.totalWaterMl` already
  performs for a single day, extended to a 7-day window. This is the
  real trend Fuel's own ADR 0038 disclosed it was deferring
  ("a genuinely computed weekly consistency figure needs... Progress-
  dashboard territory") — this phase is where that promise comes due.
  Never a per-meal pie chart or score, per Section 12's own rule.
- **Transformation** shows the latest real logged weight with a plain,
  non-alarming delta against the previous entry (no red/green pass-fail
  tone, per Section 11), a real rolling-average weight chart with raw
  points underneath (Section 12's own stated chart rule for
  Measurements), and a real list of every other currently-logged
  metric, each opening its own full trend detail.

### 3. Recovery charts real raw inputs and discloses the one missing piece honestly

Rather than reimplementing `ReadinessRuleEngine`'s formula client-side
(which would put real business logic in a widget and risk silently
drifting from the backend's own rule engine — exactly what "no shortcuts,
no business logic inside widgets" forbids), Recovery charts the two raw
readiness inputs that chart meaningfully as continuous trends (sleep
duration, heart-rate variability — energy/stress/soreness are 1-5
self-report levels, not a line-chart-shaped quantity) and shows one
`NotConnectedPlaceholder` specifically for the composite score/formula
breakdown, naming exactly what's missing rather than either faking a
score or hiding the whole dashboard behind one gap.

### 4. Workout and Reports are total, disclosed gaps

Both render `NotConnectedPlaceholder` directly for their entire segment
content — no partial charting, because no real data exists to partially
chart. This is a materially larger within-module gap than Fuel's (one
placeholder-shaped screen, Photo/Menu, inside an otherwise-real flow);
here, two of five segments are placeholders in full. Disclosed here and
in each segment's own placeholder message, not smoothed over.

### 5. Photo Check-in, Photo Comparison, and Correlations are real, reachable routes

Per this module's own directive and the precedent Fuel's Food Search/
Supplements and Train's Personal Records/Exercise Library already set:
a screen the Bible's own catalog names gets a real route and an honest
placeholder, never a silently missing menu item. `PhotoCheckinScreen`
and `PhotoComparisonScreen` are reachable from Transformation;
`InsightsScreen` (the Bible's "Insight/correlation detail") is reachable
from Recovery, since readiness-vs-training/nutrition is the most natural
correlation the Bible's own recovery-dashboard description gestures at.
Distinguished explicitly from Section 12's own "not enough data yet"
correlation rule (a real gap this module already implements correctly
for Nutrition/Recovery's own "building your first trend" states): no
amount of logged history would produce a correlation chart, because no
correlation logic exists in the backend domain layer at all — a
different kind of gap than a sample-size shortfall, and worded
differently in `InsightsScreen`'s own message to keep that distinction
honest.

### 6. No separate "Measurement entry" confirmation screen

`LogMeasurementScreen` submits and pops directly back to Progress Home,
the same pattern `LogMealScreen` already established for Fuel — Section
6.7's own flow ("Enters weight/waist/hip/etc. -> Saved as an append-only
record... sees the updated rolling-average trend") describes exactly
this: one entry screen, then straight back to the dashboard, no
intermediate confirmation step.

### 7. One new design-system chart primitive, reserved for exactly this moment

`AppLineChart` and `AppWeekHeatmap` (`lib/design/components/`) are new,
not promoted from an existing feature — this is the first phase with a
real trend to chart. `AppColors.chart1-3`/`AppSemanticColors
.chartSeries`/`chartReference` were deliberately reserved during the
design system's own build with a doc comment naming this exact moment
("a real chart phase... is what should justify inventing a new hue, not
this phase guessing ahead of it") — `AppLineChart` is that real phase,
consuming those tokens rather than adding new ones. Both components are
hand-painted via `CustomPainter` rather than a charting package, per
Section 12's own restrained-chart rule (no gradients, no legends, no
entrance animation) and this system's standing "no new dependency
without considered justification" posture. `AppIcons` gained five new
entries (`trendUp`/`trendDown`/`trendFlat`, `camera`, `compare`) for the
same reason — Transformation's weight delta and photo-related rows
needed glyphs the existing set didn't have, added following the file's
own "small, deliberate, reviewable step" discipline rather than reaching
into `Icons.*` directly.

## Consequences

**Two of five Progress dashboards (Workout, Reports) are total,
disclosed placeholders; Recovery is real-inputs-plus-one-disclosed-gap;
Nutrition and Transformation are fully real.** This is a wider spread of
gap severity within one module than any prior phase — disclosed here, in
`README.md`, and in each placeholder's own message, not smoothed into
uniform language that would make a total gap read the same as a
sample-size shortfall.

**`MockProgressRepository` is stateful**, like `MockTrainRepository`/
`MockFuelRepository` — a logged measurement must be visible on the next
fetch. It seeds ten weekly measurements (a realistic, noisy downward
weight drift, not a perfectly smooth line) plus independent 7-day
nutrition/readiness windows, reset on every app restart.

**Nutrition's and Readiness's weekly windows are Progress's own
seeded mocks, not read from `MockFuelRepository`'s state.** Both are
real-shaped derived data standing in for what `GET /api/v1/nutrition`/
`GET /api/v1/readiness` would return for the last 7 days — see
`progress_models.dart`'s library doc comment for why Progress owns this
view independently rather than reaching into Fuel's feature module.

**A disclosed, generic 130g daily protein target (`kProteinTargetGrams`)
is used**, since no personalized macro target exists anywhere in the
domain model yet — the same category of disclosed constant
`_dailyWaterTargetMl` already established for Fuel.

**Still hand-authored, structurally verified — not run in this
sandbox.** Every file in this phase inherits ADR 0002's constraint
unchanged. `log_measurement_flow_test.dart` locates form fields via
`find.widgetWithText(TextField, label)`, the same standard-but-
unverified-here idiom ADR 0037/0038 already disclosed the same risk
category for.
