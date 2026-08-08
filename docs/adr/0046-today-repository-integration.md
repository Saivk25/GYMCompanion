# ADR 0046: Today repository integration — Step 3, feature 1

- Status: accepted
- Date: 2026-08-08

## Context

Step 3 of `docs/adr/0042-production-integration-plan.md` replaces
`MockTodayRepository` with a real, backend-backed `ApiTodayRepository`
— the first of six features in this step's order (Today, Readiness,
Train, Fuel, Progress, Coach), on top of Step 1's networking layer
(`docs/adr/0043`), Step 2's auth module (`docs/adr/0044`), and this
phase's own new shared mapping convention (`docs/adr/0045`).

Researching what `TodayViewState` needs against what the backend
actually exposes surfaced a real, confirmed gap, larger than this
project's usual "one placeholder screen" disclosed gaps: `Workout`
(`backend/app/domain/workout/workout.py`) has no intensity-tier
concept, no attached exercise list, and no pre-session duration
estimate — `TodaySessionSummary`'s pre-existing `tier`/`keyLifts`/
`durationEstimateMinutes`/`oneLineSummary` fields had no backend
representation at all, not merely an unwired one. This was surfaced to
the user directly (not silently decided) given the scale of the
mismatch and its effect on Today's primary card; the user chose the
"honest reduced card" resolution below over keeping the old shape with
fabricated defaults.

## Decision

**`TodaySessionSummary` was reshaped to match what `Workout` actually
models: `name`, `plannedDate`, `goal`, `notes`.** `tier`/`keyLifts`/
`durationEstimateMinutes`/`oneLineSummary` were removed, not defaulted
— a fixed `SessionTier.standard` or an empty `keyLifts` list would be
this app inventing data the backend never produced, exactly what this
phase's "never duplicate backend business logic" / "follow the backend
exactly" rules forbid. `session_card.dart`'s `_SessionReadyCard`/
`_SessionCompletedCard` were updated to render the new fields — the one
presentation-layer change this phase makes, licensed by the driving
directive's own "do not modify presentation widgets unless integration
requires it," and it does: the old fields had nothing to map from.
`SessionCardStatus`'s five states, `TodayScreen`'s layout, and every
other card on the page are unchanged.

**Two real endpoints, fetched in parallel:** `GET /api/v1/workouts`
(`ListWorkoutsHandler`) and `GET /api/v1/readiness`
(`ListReadinessHandler`). Neither accepts a date filter — ADR 0042
Part 2's own "no pagination or filtering exists anywhere" finding —
so "is there a workout planned for today" and "was today's check-in
already submitted" are both computed by filtering the full returned
list client-side against `apiDateString(DateTime.now())`, a plain
today-vs-record-date string comparison, never a business decision.

**`hasActivePlan` means "at least one non-cancelled workout exists
anywhere,"** not "a workout exists for today specifically" — the
closest honest translation of the UX/UI Design Bible's own phrase onto
what `Workout` actually models. A user whose next session is tomorrow
still has an Active Plan; only a user with zero non-cancelled workouts
ever created sees the onboarding-continuation empty state.

**A workout planned for today maps status → `SessionCardStatus`
directly:** `completed` → `.completed`; `planned`/`in_progress` both →
`.ready` (the card has no distinct "in progress" rendering); no
matching workout at all (including a `cancelled` one for today) →
`.empty`, the same state a brand-new user with no plan sees — from the
user's perspective there is nothing to do today either way, and the
domain model has no field to represent "cancelled" distinctly.

**`readinessBand` is always `ReadinessBand.normal`; `streak` and `task`
are always `null`.** Confirmed, not guessed: no endpoint returns a
computed readiness band (the same gap `docs/adr/0039` already found for
Progress's Recovery segment), and a full sweep of `backend/app/domain/`
and `backend/app/application/` found no Habit/Streak or
Task/Recommendation aggregate exists server-side at all — not merely
unexposed. `streak`/`task` are already-nullable fields `TodayScreen`
already guards on; this is a real, honest absence, not a fabricated
one. Filed as `docs/TECH_DEBT.md`'s TD-0006 with explicit backend-side
trigger conditions, since nothing on the Flutter side can close it.

**`isOffline` is always `false`.** No local cache exists yet — Step 5
of ADR 0042 (Offline Cache), not this phase. `TodayViewState`'s
existing offline-indicator UI is unchanged and will light up correctly
once Step 5 supplies a real cached-vs-fresh signal.

**Today has no mutation endpoints, so "mutate → refetch" does not
apply to this feature.** `TodayRepository`'s interface is, and remains,
a single `fetchToday()` — `TodayScreen`'s pull-to-refresh and error-
retry both already call `TodayController.refresh()`, which was not
changed.

## Consequences

`lib/features/today/infrastructure/dto/workout_dto.dart` and
`readiness_summary_dto.dart` are the first real consumers of
`docs/adr/0045`'s mapping convention. Neither DTO mirrors its full
backend response — each declares only the fields `ApiTodayRepository`
actually reads, per that ADR's own "a DTO models what a feature
consumes" rule; a complete `WorkoutDto`/`ReadinessDto` mirroring every
field belongs to Train's and Readiness's own future repositories.

`MockTodayRepository` was not deleted — it remains
`test/features/today/today_screen_test.dart`'s fixture, its own doc
comment updated to disclose it is no longer the production
implementation and that its `streak`/`task`/`goal`/`notes` values are
illustrative only.

Not yet verified by execution — same disclosed constraint as every
prior phase (ADR 0002). `test/core/mapping/` (the shared convention)
and `test/features/today/api_today_repository_test.dart` (this
feature, using the existing `FakeHttpClientAdapter` from
`test/core/network/fakes/`) are structurally verified but not executed.
