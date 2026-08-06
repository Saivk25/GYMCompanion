# ADR 0037: Train module — Pre-session, Active Workout, Summary, and two honest gaps

- Status: accepted
- Date: 2026-08-06

## Context

Today (ADR 0036) established the pattern every later feature screen
inherits: `domain/application/infrastructure/presentation`, a repository
interface behind a Riverpod provider, a disclosed mock implementation,
and two-level loading/error handling. This phase applies that pattern to
Train — the module the user's own directive names in the most detail of
any phase so far, listing eleven screens by name (Workout Home, Today's
Workout, Workout Details, Exercise List, Exercise Detail, Active
Workout, Exercise Logging, Rest Timer, Session Progress, Session
Summary, Personal Records, Workout History) and requiring every one of
them to exist, in some form, with no fake data and no fake success.

Two research findings shaped this phase before any screen was built:

1. **The UX/UI Design Bible's own Section 5.2 spec for "Active Workout
   Session" describes exercise logging, the rest timer, and session
   progress as facets of *one* screen**, not three separate
   destinations — its fourteen-field spec (Purpose/Primary actions/
   Displayed info/Interaction priority/every named state) is written as
   a single screen throughout. The user's eleven-item list and the
   Bible's own screen catalog are not actually in conflict once read
   this way — the list names *concepts*, the catalog names *screens*,
   and Active Workout is the one screen four of those concepts belong
   to.
2. **The backend has no exercise-catalog endpoint, no dedicated
   personal-records endpoint, and no exercise-id-to-name resolution at
   all.** `backend/app/api/routes/v1/` has `goal.py`, `workout.py`,
   `nutrition.py`, `progress.py`, `readiness.py` — no `exercise.py`.
   `ExercisePerformanceResponse` (`backend/app/api/schemas/workout.py`)
   carries `exercise_id`, never a name. `progress.py`'s routes are
   generic progress-record CRUD, not PR computation. This is not "the
   Flutter HTTP client isn't wired yet" (Today's own gap, covered
   entirely by a mock repository) — it is "no backend concept exists to
   wire to yet," which is exactly the distinction the user's own
   instruction draws: *"If backend functionality is unavailable, show
   an honest, polished placeholder."*

## Decision

### 1. Six real routes, not eleven, mapping the user's list onto the Bible's screens

| User's concept | Where it lives |
|---|---|
| Workout Home | `TrainHomeScreen` (`/train`) |
| Today's Workout, Workout Details, Exercise List | `PreSessionScreen` (`/train/pre-session/:workoutId`) |
| Active Workout, Exercise Logging, Rest Timer, Session Progress | `ActiveWorkoutScreen` (`/train/session/:sessionId`) |
| Session Summary | `SessionSummaryScreen` (`/train/session/:sessionId/summary`) — also serves History's "session detail (past)" |
| Personal Records | `PersonalRecordsScreen` (`/train/records`) |
| Workout History | Train Home's own "History" in-page tab, per Bible Section 4 ("In-page tabs... within Train: This Week / History / Library") — not a seventh route |
| (Bible's own "Exercise detail") | `ExerciseDetailScreen` (`/train/exercise/:exerciseId`), linked from Active Workout's "Cues" action |

Every concept in the user's list is reachable; nothing was dropped.
Bundling logging/rest-timer/progress into Active Workout is not a
scope reduction — it is following the Bible's own fourteen-field spec
for that screen literally, and it is what "reuse whenever possible... if
duplication appears, improve the component library, not the screen"
means applied to information architecture, not just widgets: three
near-identical logging screens differing only by which sub-panel is
visible would have been the duplication that instruction warns against.

### 2. Session Summary is one screen, not two

The Bible's catalog lists "Session summary" ("Post-session recap...
Return to Today") and "Session detail (past)" ("Full detail of a
completed session... Return to history") as separate rows — but the
*content* each describes is the same data (`TrainSession`, fully
populated), differing only in which exit action makes sense from where
the user arrived. `SessionSummaryScreen` takes one `bool
cameFromActiveSession` and switches only its primary button's label and
destination; every other pixel is identical. `TrainHistoryTile` pushes
the route with no `extra` (defaulting to `false`); `ActiveWorkoutScreen.
_endSession` pushes it with `extra: true` after `completeSession`
succeeds.

### 3. Two backend gaps get a real screen with an honest placeholder, not fake data

`ExerciseDetailScreen` and `PersonalRecordsScreen` are real, reachable,
fully design-system-correct screens — but everything below what's
already known (an exercise's name, if the caller had one) is
`NotConnectedPlaceholder` (`presentation/widgets/not_connected_
placeholder.dart`), a shared wrapper around `AppEmptyState` built once
and reused by both screens plus Train Home's Library tab, rather than
three screens each inventing their own wording for the same disclosure.
`TrainPersonalRecord` exists in `domain/train_models.dart` — modeled
ahead of the backend work so a future real repository has a shape to
fill in — but nothing constructs one today; inventing plausible PR
numbers to make the screen look populated would have been exactly the
"no fake data, no fake success" violation the user's directive names.

Workout History did **not** get this treatment, despite `GET /workout-
sessions/{id}` having no list variant — because `GET /workouts` (list)
does exist, and a real repository can serve History from "past workouts,
resolved to their sessions on open" without any new backend endpoint.
Only a genuinely missing *capability* (no exercise catalog exists to
browse; no PR computation exists to show) gets the placeholder
treatment; a missing *client wiring* around an endpoint that already
exists does not.

### 4. Two design-system extensions, both load-bearing, neither improvised inline

- **`AppSegmentedControl`** (`design/components/app_segmented_control.
  dart`) — the Bible names "in-page tabs" as a pattern (Progress's five
  dashboards, Train's This Week/History/Library) but nothing had built
  it yet. A pill track with equally-weighted pill segments, reusing
  `AppSemanticColors.selected*` rather than a new color, `AppRadius.full`
  for exactly the "toggle track" case that token's own doc comment
  reserves pill shapes for.
- **`AppTextField`** (`design/components/app_text_field.dart`) — Train's
  set-log row (weight/reps/RPE) is this app's first real text-input
  requirement. `AppTheme` already had a complete `inputDecorationTheme`
  (Step 6/`app_theme.dart`) that no widget had exercised yet; this
  component supplies only the label/semantics/density contract every
  field should share, the same division `AppButton` has with the
  theme's button styles — it does not re-decide any color or border.

Both extensions were built *because* a real screen needed them, not
spec-ahead-of-need — matching how ADR 0036's readiness-band work
extended nothing it didn't have to.

### 5. `SessionTier` moves to `lib/shared/domain/`

Train's Pre-session tier choice and Today's already-shipped tier display
are the same three-value vocabulary. Rather than let Train define a
second, identical enum, `SessionTier` (with a new `.description` getter
Pre-session's explicit choice needs but Today's read-only display never
did) now lives in `shared/domain/session_tier.dart`; `today_models.dart`
imports and re-exports it so no existing call site changed. This is the
"if duplication appears, improve the component library, not the screen"
instruction applied to a domain type, not just a widget.

### 6. `ActiveSessionController`'s mutations rethrow instead of guarding

`TrainHomeController.refresh` uses `AsyncValue.guard` (matching
`TodayController`) because a Home re-fetch failing really should show
the page-level error state. `ActiveSessionController.logSet/completeSet/
completeSession` deliberately do **not** — a guarded failure would flip
the whole screen's `AsyncValue` to `.error`, and `ActiveWorkoutScreen`'s
top-level `state.when(...)` would render a full-page error over one
failed set log in an otherwise-fine session, exactly the "blocking error
screen" this app's design philosophy rejects. These three methods
rethrow with `state` left untouched; `ActiveWorkoutScreen` catches
locally and shows a narrow `SnackBar` — the same card-scoped-error
precedent `SessionCard`'s own error state set for Today, applied to a
mutation instead of a fetch.

### 7. Train's sub-screens are root-navigator routes, not nested branch routes

`StatefulShellRoute.indexedStack` keeps `AppShell`'s single `Scaffold`
(global top bar, five-tab bottom `NavigationBar`) mounted for anything
pushed onto a branch's own nested `Navigator`. Correct for `/train`
itself; wrong for Pre-session/Active Workout/Summary/Exercise Detail/
Records — a workout logging screen with the tab bar still tappable
underneath risks an accidental exit mid-session, and none of these read
as "still the Train tab" the way Today's FAB sheet does. Each of the six
new routes in `app_router.dart` sets `parentNavigatorKey:
_rootNavigatorKey`, pushing onto the root `Navigator` above the entire
shell; each screen below builds its own `Scaffold`/`AppBar` (back arrow,
title) accordingly, rather than inheriting the shell's chrome.

### 8. Today's "Start session" is now real navigation

`SessionCard.onStartSession` previously showed the "not built yet"
snackbar every deferred Today action used (ADR 0036, Decision 7). It now
calls `context.push('/train/pre-session/workout-today')` — real
navigation into the module this phase built, directly serving the user's
own stated goal ("the user should never feel like they're entering
another application"). `'workout-today'` is `MockTrainRepository`'s own
fixed id for today's workout; `TodaySessionSummary` has no `workoutId`
field yet (it predates Train), so this is a disclosed, temporary
coupling — commented at its declaration — not a silent hack. A real
repository pass adds a real `workoutId` to `TodaySessionSummary` and
this literal goes away.

## Consequences

**Every screen the user named is reachable and real**, with honest
states throughout (loading skeletons matching real layout, never a bare
spinner except `AppLoadingIndicator`'s reserved genuinely-indeterminate
cases; empty states framed as normal, not error; narrow, card-scoped
errors that never blank a whole screen; two disclosed not-connected
placeholders where a backend capability genuinely does not exist yet).

**`MockTrainRepository` is stateful, unlike `MockTodayRepository`.**
Logging a set must be visible on the next rebuild, so this mock keeps an
in-memory `Map<String, TrainSession>` mutated by `logSet`/`completeSet`/
`completeSession` — still fully disclosed (its own doc comment), still
reset on every app restart, still replaced wholesale by a provider
override once a real API client exists.

**A real API client, local cache, and offline sync are still not
built**, exactly as ADR 0036 already disclosed for Today — this phase
inherits that gap rather than closing it.

**Personal Records and the Exercise Library remain unbuilt in substance**
until a backend endpoint exists for either — this was a deliberate scope
boundary, not an oversight, and is the correct reading of "if backend
functionality is unavailable, show an honest, polished placeholder"
rather than a reason to skip the screens entirely.

**Still hand-authored, structurally verified — not run in this sandbox.**
Every file in this phase inherits ADR 0002's constraint unchanged. One
elevated risk specific to this phase: `ActiveWorkoutScreen` runs a real
`Timer.periodic` for its elapsed-time display, which makes
`active_workout_screen_test.dart` structurally reliant on bounded
`pump(duration)` calls instead of `pumpAndSettle()` past the point that
screen mounts (that test file's own doc comment explains why). This
reasoning could not be empirically confirmed by actually running the
test suite — the highest-risk single item in this phase's own
Verification section.
