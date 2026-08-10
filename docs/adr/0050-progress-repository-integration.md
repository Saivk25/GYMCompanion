# ADR 0050: Progress repository integration — Step 3, feature 5

- Status: accepted
- Date: 2026-08-10

## Context

Step 3 of `docs/adr/0042-production-integration-plan.md`'s fifth
feature: replace `MockProgressRepository` with a real, backend-backed
`ApiProgressRepository`, reusing `docs/adr/0045`'s shared mapping
convention exactly as established by Today/Readiness/Train/Fuel.

Unlike Fuel, this integration **did** surface a genuine domain/UI
question, raised via `AskUserQuestion` before implementation continued,
per this project's own "stop and ask on a domain-model mismatch"
convention:

**Question 1 — discarded warnings.** `POST /api/v1/progress`
(`RecordProgressHandler`, read in full) evaluates
`ProgressEvaluationRuleEngine` (`ConsistencyRule`/`PlateauRule`/
`MeasurementTrendRule`) against the user's full check-in history on
every write and returns its findings as real `IdResponse.warnings` —
but `ProgressRepository.logMeasurement`'s existing interface returned
only `Future<ProgressEntry>`, with no way to carry those warnings back
to the caller at all. Silently dropping them would have discarded real
advisory data the same way an early draft of `ApiFuelRepository` did
not. The user chose **"Wire it up"**: extend the interface with a
`ProgressLogResult{entry, warnings}` return type, mirroring
`FuelLogResult`/`ReadinessCheckInResult`.

**Question 2 — where do the warnings go?** Every prior module with real
warnings (Readiness, Fuel, Train) pushes them into `CoachSignalLog`.
Wiring Progress the same way turned out to be architecturally blocked:
`CoachModule` (`lib/shared/domain/coach_signal.dart`) is a deliberately
closed three-value enum (`recovery`, `nutrition`, `training`) whose own
doc comment states outright that there is no fourth value for
Progress's own rule-engine output — a scope decision `docs/adr/0041-
coach-module.md` made before this repository existed, not something
this phase introduced. Inventing a fourth `CoachModule` value to force
a fit would have reopened ADR 0041's own scope decision without the
user's sign-off. The user chose **"Surface warnings on Progress's own
screen only"**: render the real warnings inline on Progress Home's
Transformation segment, mirroring `ReadinessHomeScreen`'s existing
"Advisory notes from your last check-in" pattern, rather than
cross-posting into a module whose documented scope excludes them.

No other domain/UI mismatch came up this phase.

## Decision

**Three endpoints, no new ones, one interface change.** `fetchHome()`
issues three parallel `GET`s — `/api/v1/progress`, `/api/v1/nutrition`,
`/api/v1/readiness` — none of them Progress-specific; the same three
endpoints Fuel/Readiness/Today already use individually.
`logMeasurement()` → `POST /api/v1/progress` (`RecordProgressHandler`),
now returning `Future<ProgressLogResult>` instead of
`Future<ProgressEntry>` — the one interface change this phase made,
justified by Question 1 above.

**`ProgressEntryDto` mirrors the full `ProgressResponse`**, per
`docs/adr/0045`'s "a DTO reads every real field" rule. `unit`/`source`
are read and passed through as raw wire strings, not mapped through a
`fromWire` enum factory — `ProgressEntry.unit`/`.source` were never
promoted to real Dart enums in the first place (`progress_models.dart`'s
own doc comment), so there is no enum to map onto.

**`NutritionSummaryEntryDto`/`ReadinessSummaryEntryDto` are Progress's
own narrow view types**, not `FuelEntryDto`/`ReadinessEntryDto` reused
across a feature boundary — `progress_models.dart`'s own library doc
comment already anticipated and endorsed this shape before this
repository existed. `aggregateNutritionWeek`/`aggregateReadinessWeek`
are real client-side aggregations (sum of real per-day protein/water;
latest-recorded entry per day for sleep/HR/HRV) over the full,
unfiltered nutrition/readiness lists — no backend trend endpoint
exists, so this is genuine arithmetic over real data, never a
fabricated series.

**`unit`/`source` are hardcoded on write, not invented.**
`RecordProgressRequest.unit`/`.source` are *required* fields, unlike
Readiness's/Fuel's optional `source`. `ApiProgressRepository` sends
`unit: 'metric'`, `source: 'manual'` on every `logMeasurement` call —
not a new decision this phase invented: `MockProgressRepository`
already hardcoded the identical two values on every entry it ever
constructed, and `MeasurementMetric.unitSuffix`'s own doc comment
already discloses no personalized unit preference exists anywhere in
this client. `source: 'manual'` is not a guess either — every entry
this client can create today genuinely was typed in by hand.

**Logged entries are honest echoes, plus real warnings.** `POST
/api/v1/progress` returns only `IdResponse{id, warnings}` — the same
constraint every prior `ApiXRepository`'s mutation faced. The echoed
`ProgressEntry` is built from the submitted parameters plus the real
assigned `id`, since neither `LogMeasurementScreen` nor
`ProgressHomeController.logMeasurement` reads the returned entity's
fields (confirmed by reading both call sites) — both discard it and
re-fetch `fetchHome()`. `warnings`, unlike prior phases, is not
discarded — see Decision/Question 1 above.

**No new backend capability gap found beyond what was already
disclosed.** `ProgressHomeScreen`'s Workout/Reports/Correlations
sections were already permanent, disclosed `NotConnectedPlaceholder`s
before this phase — no analytics/report/photo/correlation route exists
anywhere in `backend/app/api/routes/v1/` — and remain untouched.

## Consequences

`MockProgressRepository` was not deleted — kept as
`test/features/progress/`'s fixture (`progress_home_screen_test.dart`,
`log_measurement_flow_test.dart`), updated in step with the interface
change: it now also returns `ProgressLogResult`, with two fixed,
clearly-illustrative advisory strings on the first logged measurement
only, mirroring `MockReadinessRepository.submitCheckIn`'s own disclosed
posture.

`ProgressTransformationSection` gained a `lastLogWarnings` parameter
and an inline "Advisory notes from your last check-in" rendering block,
wired from `ProgressHomeViewState.lastLogWarnings` — real,
non-fabricated `ProgressEvaluationRuleEngine` output is still surfaced
to the user, just not cross-posted to `CoachSignalLog`.
`ProgressHomeController.logMeasurement` deliberately does **not** call
`coachSignalLogProvider` — this is intentional, not an oversight, per
Question 2's decision above.

No `docs/TECH_DEBT.md` entry was warranted — every field this
repository maps corresponds to a real backend value already covered by
existing disclosures (the Workout/Reports/Correlations placeholders
predate this phase).

Not yet verified by execution — same disclosed constraint as every
prior phase (ADR 0002); no `flutter`/`dart` toolchain is available in
this working environment. `test/features/progress/
api_progress_repository_test.dart` (structurally verified but not
executed) covers: `fetchHome`'s three-endpoint parallel fetch and
field mapping, `aggregateNutritionWeek`/`aggregateReadinessWeek`'s real
summation/latest-entry-selection behavior, and `logMeasurement`'s
selective body construction (hardcoded `unit`/`source`, only submitted
measurement fields) plus real-warning propagation through
`ProgressLogResult`.
