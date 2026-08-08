# ADR 0048: Train repository integration — Step 3, feature 3

- Status: accepted
- Date: 2026-08-08

## Context

Step 3 of `docs/adr/0042-production-integration-plan.md`'s third
feature: replace `MockTrainRepository` with a real, backend-backed
`ApiTrainRepository`, reusing `docs/adr/0045`'s shared mapping
convention exactly as established — no feature-specific mapping
utilities were introduced beyond a `WorkoutStatus.fromWire`/
`SessionStatus.fromWire` pair, which reuses the exact `fromWire`
convention `ReadinessSource.fromWire` (`docs/adr/0047`) already
established, not a new one.

Unlike Today and Readiness, this integration surfaced three genuine
backend capability gaps, each explicitly surfaced to the user and its
handling approved before implementation, per this phase's own "if
another mismatch between the UI model and backend contract is
discovered, stop and surface it before changing the presentation layer"
instruction:

1. **No exercise catalog.** `grep -rli "exercise" backend/app/api`
   finds no `exercise.py` route file at all. `LogExerciseSetHandler`
   (`backend/app/application/workout/handlers/
   log_exercise_set_handler.py`) validates any submitted `exercise_id`
   against the real seeded `Exercise` table and 404s on an id it
   doesn't recognize — there is no way for this client to discover or
   safely submit a real `exercise_id` for logging.
2. **No session-history list endpoint.** `backend/app/api/routes/v1/
   workout.py`'s ten endpoints include `GET /workout-sessions/{id}`
   (single) but no `GET /workout-sessions` (list).
3. **No `tier` concept anywhere in the backend.** Same root cause ADR
   0046 already found for Today's `tier`/`estimatedMinutes`/
   `plannedExerciseNames`: `StartWorkoutSessionRequest`
   (`backend/app/api/schemas/workout.py`) has exactly one field,
   `session_date`.

Resolution for each was decided with the user, not unilaterally:

- Gap 1 → **"Defer Train's Active Workout logging; integrate the rest."**
  `ApiTrainRepository.logSet`/`.completeSet` throw
  `TrainLoggingUnavailableException` synchronously, before any network
  call — the user's explicit choice over silently sending a request
  that could only ever fail. `ActiveWorkoutScreen` catches this specific
  exception type to show accurate, permanent-unavailability copy
  instead of the generic "try again" phrasing every other failure path
  in this screen still uses for genuine transient errors.
- Gap 2 → **"History is always empty, no additional messaging."**
  `TrainHomeViewState.history` is always `[]`; `TrainHomeScreen`'s
  existing `AppEmptyState` for an empty history list already renders
  correctly, so zero presentation changes were made.
- Gap 3 → resolved by my own judgment, applying the user's own
  generalized "continue to surface backend capability gaps honestly
  rather than filling them with defaults" instruction (given after
  approving Today's `TodaySessionSummary` reduction) to the same
  category of gap recurring in Train: `TrainWorkout.tier`/
  `.estimatedMinutes`/`.plannedExerciseNames` were removed from the
  domain model entirely, mirroring `TodaySessionSummary`'s own
  resolution exactly. `PreSessionScreen`'s `TierPicker`, however, was
  *kept* — a deliberately different call from Today's, since a tier
  *selection* affordance costs nothing to leave visible and inert
  (`ApiTrainRepository.startSession` accepts but never transmits it),
  where Today had no equivalent "picker still worth keeping" case. This
  judgment call was not separately re-confirmed by the user before
  implementation and should be corrected if reviewed differently.

## Decision

**Five endpoints, no interface change.** `fetchHome()` →
`GET /api/v1/workouts`, filtered client-side into a `thisWeek` list
(non-cancelled, non-completed, `plannedDate` within 6 days of today —
the backend supports no date-range query parameter at all, ADR 0042
Part 2's own "no pagination or filtering exists anywhere" finding
applied here) and an always-`[]` `history` (gap 2).  `fetchWorkout()` →
`GET /api/v1/workouts/{id}`. `startSession()` → `POST /api/v1/workouts/
{id}/sessions` (body: `session_date` only, gap 3), then mutate → refetch
via `GET /api/v1/workout-sessions/{id}`. `fetchSession()` → the same GET
directly. `completeSession()` → `POST /api/v1/workout-sessions/{id}
/complete`, then the same mutate → refetch. `logSet`/`completeSet` never
reach the network (gap 1).

**`TrainWorkoutDto`/`TrainSessionDto`/`ExercisePerformanceDto`/
`ExerciseSetDto` mirror their respective backend response schemas
field-for-field**, per `docs/adr/0045`'s "a DTO reads every real field"
rule — including `WorkoutResponse.cancelled_at`, which
`TrainWorkoutDto` reads but `TrainWorkout` (the domain type) has no
field for, since no Train screen renders a cancellation timestamp and
`status` already distinguishes cancelled from every other state.

**`workoutName` is resolved by a real second fetch, never fabricated.**
`WorkoutSessionResponse` carries only `workout_id`. Every mutate →
refetch path and `fetchSession()` itself route through one shared
helper, `_fetchFullSession`, which does `GET /workout-sessions/{id}`
then `GET /workouts/{workout_id}` and only then constructs the domain
`TrainSession` — an extra real round trip, not a shortcut, matching
`TrainSession.workoutName`'s own doc comment's stated reasoning.

**`ExercisePerformanceDto.toDomain()` falls back to the raw
`exerciseId` as `exerciseName`** — no fabricated label, no attempt to
guess a name from context; this is the same "denormalize honestly, or
fall back to the raw id" posture the domain model's own doc comment
already described before this repository existed. `targetSets`/
`targetReps`/`targetWeight` are left `null` — `ExercisePerformanceResponse`
carries no progression-engine suggestion; inventing one would
reimplement `ExerciseRecommendationRuleEngine` client-side, exactly
what this phase's "never duplicate backend business logic" rule
forbids.

**`ExerciseRecommendationRuleEngine`/`ProgressiveOverloadRuleEngine`/
`TrainingLoadRuleEngine` are never reimplemented or approximated
client-side.** `completeSession`'s real warnings come from `POST
.../complete`'s own `IdResponse.warnings` — the exact strings the real
rule engines produced server-side, returned unchanged and pushed into
`CoachSignalLog` unchanged (`ActiveSessionController.completeSession`,
`application/train_controller.dart` — this method's own code did not
change; only the repository beneath it did).

**`TrainLoggingUnavailableException`** (new type,
`application/train_controller.dart`, alongside the `TrainRepository`
interface it is thrown by) is the one new abstraction this phase
introduced beyond the DTOs — deliberately not a mapping utility, and
deliberately placed in the application layer rather than
infrastructure, so `ActiveWorkoutScreen` (presentation) can catch it by
type without importing anything from `infrastructure/`.

## Consequences

`MockTrainRepository` was not deleted — kept as `test/features/train/`'s
fixture, doc comment updated to disclose it is no longer the production
implementation (mirroring `MockTodayRepository`'s and
`MockReadinessRepository`'s own updated doc comments). Its four
`TrainWorkout(...)` construction sites had their now-nonexistent
`tier`/`estimatedMinutes`/`plannedExerciseNames` arguments removed to
match the reduced domain type; its own logging/session-mutation
behavior (a genuinely stateful in-memory mock, unlike the other two
pure-read mocks) is otherwise unchanged.

`docs/TECH_DEBT.md`'s new **TD-0007** records all three gaps and their
trigger conditions for closing each (a real exercise-catalog endpoint,
a real session-list endpoint, and a real backend tier/intensity field,
respectively) in one place, mirroring TD-0006's multi-item structure
for Today's own three gaps.

Not yet verified by execution — same disclosed constraint as every
prior phase (ADR 0002). `test/features/train/
api_train_repository_test.dart` (structurally verified but not executed)
covers: `fetchHome`'s this-week filtering and always-empty history,
`fetchWorkout`, `startSession`'s session_date-only body and tier
omission, `fetchSession`'s workoutName resolution and exerciseName
fallback, `completeSession`'s body and real-warning propagation, and
both `logSet`/`completeSet` throwing `TrainLoggingUnavailableException`
with zero recorded HTTP requests.
