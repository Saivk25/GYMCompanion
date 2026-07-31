# ADR 0024: Workout Application Use Cases — multi-aggregate orchestration, rule engines invoked from the Application Layer, and why Workout/WorkoutSession stay separate aggregates

- Status: accepted
- Date: 2026-07-31

## Context

Sprint 4, Phase 3 asked for the second concrete consumer of the
Application Layer Foundation (`docs/adr/0022-application-layer-
foundation.md`) and the first to coordinate more than one aggregate:
ten command/query handlers built on top of `Workout`
(`app.domain.workout`) and `WorkoutSession`
(`app.domain.workout_session`), containing "NO business rules" of
their own, orchestrating repositories, a `UnitOfWork`, and — new in
this phase — deterministic Rule Engines. The task named a fixed file
list (seven commands, three queries, two DTOs, ten handlers) and three
required ADR topics: why handlers orchestrate multiple aggregates, why
rule engines are invoked from the Application Layer, and why `Workout`
and `WorkoutSession` remain separate aggregates.

Two structural gaps existed before any handler could be written, both
resolved the same way `docs/adr/0023-user-application-use-cases.md`
resolved its own gaps — by extending the narrowest thing that actually
needed extending, not by working around it in a handler:

1. **Neither `WorkoutRepository` nor `WorkoutSessionRepository`
   declared anything beyond `get`/`add`/`remove`.** `ListWorkoutsQuery`
   needs "every Workout for a User," and
   `CompleteWorkoutSessionHandler`'s rule-engine orchestration (below)
   needs "every WorkoutSession for a User" to build a training
   history. Both repository modules' own prior docstrings had already
   anticipated this ("add one only once a real caller needs it, not
   speculatively") — this phase is that real caller.
2. **The task named five example Rule Engines
   (`SafetyRuleEngine`, `ReadinessRuleEngine`,
   `ProgressiveOverloadRuleEngine`, `TrainingLoadRuleEngine`,
   `ExerciseRecommendationRuleEngine`) but the task's own required
   repository list for this phase — `WorkoutRepository`,
   `WorkoutSessionRepository`, `ExerciseRepository` (lookup only),
   `UserRepository` (when needed) — has no Safety or Readiness
   repository access at all.** Wiring in an engine this phase has no
   data source for would mean inventing empty/placeholder context
   fields with no real evidence behind them.

## Decision

1. **`list_by_user(user_id) -> Sequence[...]` is added as a new
   abstract method to both `WorkoutRepository`
   (`app.domain.workout.repository`) and `WorkoutSessionRepository`
   (`app.domain.workout_session.repository`), with no persistence
   implementation — the identical "declare the contract now, implement
   it in `app.infra` later" split every repository interface in this
   codebase already follows.** `ListWorkoutsHandler` is the concrete
   caller for the former; `CompleteWorkoutSessionHandler`'s
   history-building (decision 5) is the concrete caller for the
   latter. Neither method promises an order — a caller needing one
   (e.g. by `planned_date`) sorts the result itself, the same
   "caller-supplied ordering" trust `TrainingLoadRuleContext.
   from_summaries()` already places in its own caller.

2. **Only `ExerciseRecommendationRuleEngine`,
   `ProgressiveOverloadRuleEngine`, and `TrainingLoadRuleEngine` are
   wired into this phase's handlers; `SafetyRuleEngine` and
   `ReadinessRuleEngine` are not — a deliberate scope boundary, not an
   oversight.** `LogExerciseSetHandler` evaluates
   `ExerciseRecommendationRuleEngine` with a minimal context — only
   the required `exercise: ExerciseContext` field populated, every
   other field (`goal`, `safety_result`, `readiness_result`,
   `progressive_overload`, `declared_restrictions`,
   `available_equipment`, `recent_movement_patterns`) left at its
   documented default, because no Goal/Safety/Readiness repository
   access exists in this phase's own required repository list.
   `CompleteWorkoutSessionHandler` evaluates both
   `ProgressiveOverloadRuleEngine` and `TrainingLoadRuleEngine` from
   the user's session history (decision 5). A future phase that adds
   Safety/Readiness repository access can populate the remaining
   `ExerciseRecommendationRuleContext` fields without changing this
   phase's handlers' shape — the context type already has room for
   them.

3. **Rule engines are invoked from the Application Layer, immediately
   after a successful `commit()`, and their output is surfaced only as
   `ApplicationResult.warnings` — never as a reason to fail the
   workflow.** Every engine wired into this phase
   (`ExerciseRecommendationRuleEngine`, `ProgressiveOverloadRuleEngine`,
   `TrainingLoadRuleEngine`) documents itself as evaluation-only and
   incapable of blocking anything on its own authority — the same
   "evaluation-only, cannot itself block" discipline
   `docs/adr/0018-safety-rule-engine-composition-and-authority.md` and
   `docs/adr/0020-training-load-supplied-summaries.md` already
   established for their own engines. The Domain Layer's rule packages
   have no repository or service access of their own by design
   (`docs/adr/0013-rule-engine-foundation.md`) — something has to
   assemble a `RuleContext` from live aggregate state and hand it to
   `RuleEngine.evaluate()`, and the Application Layer is the only layer
   positioned to do that: it already holds the loaded aggregates, the
   `UnitOfWork`, and (via `list_by_user()`) the historical data these
   two trend-based engines need, while the Domain Layer's rule packages
   correctly stay ignorant of persistence entirely. A small private
   `_advisory_warnings(result: RuleResult) -> tuple[str, ...]` helper —
   duplicated in `log_exercise_set_handler.py` and
   `complete_workout_session_handler.py` rather than factored into a
   shared module — formats `RuleResult.recommendations` as
   `f"[{severity.value}] {message}"` strings; kept small and local
   rather than promoted to `app.application.shared` because two
   call sites sharing one three-line function is not yet the "second
   real need" this codebase's modules consistently wait for before
   generalizing.

4. **`Workout` and `WorkoutSession` remain separate aggregates
   (`docs/adr/0006-workout-aggregate-first-increment.md` and
   `docs/adr/0008-workout-session-execution-record.md` already
   established this; this phase is the first to build handlers that
   make the consequence concrete).** Three pieces of evidence from this
   phase support keeping them separate rather than merging or
   collapsing one into the other:
   - **Neither aggregate can see the other's state**, which is exactly
     why `StartWorkoutSessionHandler` and `CompleteWorkoutSessionHandler`
     — not `Workout` or `WorkoutSession` themselves — are the only
     place the cross-aggregate rule "a session cannot start under a
     Completed/Cancelled workout" can be enforced (decision 5 below).
     If they were one aggregate, this check would collapse into an
     ordinary in-aggregate invariant; because they are two, it is
     necessarily an Application Layer concern.
   - **`CancelWorkoutCommand` deliberately does not cascade** to any
     `WorkoutSession` executing under the cancelled workout —
     `CancelWorkoutHandler` touches only `WorkoutRepository`, never
     `WorkoutSessionRepository`. Cancelling tomorrow's planned workout
     should not rewrite an execution record already in progress or
     completed; a merged aggregate would make this non-cascading
     behavior far more awkward to express than two aggregates with
     independent lifecycles naturally allow.
   - **They complete on different, independently-supplied inputs.**
     `WorkoutSession.complete()` requires a `SessionDuration` (the
     execution record's own elapsed time); `Workout.complete()`
     requires a `WorkoutDuration` (a different value object, with a
     looser "must not be negative" rule versus `SessionDuration`'s
     stricter "must be positive," per each type's own docstring).
     `CompleteWorkoutSessionHandler` bridges the two explicitly —
     `WorkoutDuration(value=request.duration.value)` — rather than the
     domain model assuming they are the same measurement, because they
     are two different aggregates' own value objects that merely
     happen to share a scalar type today.

5. **Both multi-aggregate handlers (`StartWorkoutSessionHandler`,
   `CompleteWorkoutSessionHandler`) advance the parent `Workout`
   idempotent-forward: they call `workout.start()`/`workout.complete()`
   only if the workout is not already in the target state.** This is
   orchestration bookkeeping, not a reimplementation of `Workout`'s own
   transition legality — `Workout._transition_to()` still owns, and
   remains the only place that decides, which transitions are legal at
   all; the idempotent-forward check only prevents a handler from
   calling a legal-sounding method a second time when the aggregate has
   already moved past that point (e.g. starting a second session under
   a workout already `InProgress`, or completing a session whose
   sibling session already completed the same workout). Without this
   check, a second legitimate session under one workout would trigger a
   spurious `DomainInvariantViolationError` on an action the caller has
   every right to perform. `StartWorkoutSessionHandler` additionally
   rejects the command outright — before constructing anything — if the
   loaded `Workout.status` is `Completed` or `Cancelled`, which is the
   cross-aggregate consistency check named in decision 4.

6. **`CreateWorkoutHandler` and `StartWorkoutSessionHandler` both keep
   an `except DomainInvariantViolationError: raise` guard even though
   neither can currently reach it — kept for defensive consistency with
   every other mutating handler's "always re-raise, never convert"
   policy (`docs/adr/0023`, decision 3), not because either path is
   reachable today.** `Workout.plan()`'s own invariant (a tz-aware
   `planned_at`) is guaranteed by every `Clock` implementation in this
   codebase, and every other field arriving at `CreateWorkoutHandler`
   is a value object already validated at construction, before the
   handler ever runs — so its guard is presently unreachable, marked
   `# pragma: no cover` with an explanatory comment rather than removed.
   `StartWorkoutSessionHandler` similarly already checks
   `workout.status` before calling `session.start()`/`workout.start()`,
   so neither call can hit an illegal transition on any path reaching
   its own guard. Every other mutating handler in this phase
   (`UpdateWorkoutHandler`, `CancelWorkoutHandler`,
   `LogExerciseSetHandler`, `CompleteExerciseSetHandler`,
   `CompleteWorkoutSessionHandler`) *does* have a reachable invariant
   violation exercised by a dedicated test (e.g. updating/cancelling a
   Completed workout, completing an unknown set number, completing a
   still-`Planned` session) — this decision only concerns the two
   handlers where the domain model's own guarantees happen to make the
   guard currently dead code.

7. **`WorkoutDTO`/`WorkoutSessionDTO`/`ExercisePerformanceDTO` are
   distinct types from `app.domain.workout.context.WorkoutContext`/
   `app.domain.workout_session.context.WorkoutSessionContext`/
   `ExercisePerformanceContext`, for the identical reasoning
   `docs/adr/0023` gives for `UserDTO` versus `UserContext`.** The
   `*Context` types are scoped to future domain services (rule
   engines) and are explicitly one-directional and never persisted;
   the `*DTO` types answer what a caller of `GetWorkoutQuery`/
   `GetWorkoutSessionQuery`/`ListWorkoutsQuery` receives back. Two
   consumers with different reasons to change independently stay two
   types.

8. **`LogExerciseSetCommand` carries no `performance_id` — the handler
   finds an existing `ExercisePerformance` for `exercise_id` within the
   loaded session, or creates one via `WorkoutSession.add_exercise()`,
   treated as application-level bookkeeping, not business logic.** The
   actual legality of adding an exercise to a session is still entirely
   `WorkoutSession.add_exercise()`'s own `_ensure_mutable()` call to
   make; this handler only decides *which* existing performance (if
   any) to reuse, sparing a caller from needing to track whether this
   is the first set logged for a given exercise in a given session.
   The resulting mypy definite-assignment problem — `performance_id` is
   assigned only inside the `try`, consumed after it, with no safe
   trivial default the way `events`/`warnings` have (`()`) — is
   resolved with a pre-declared `performance_id:
   ExercisePerformanceId | None = None` followed by a post-`try`
   `if performance_id is None: raise AssertionError(...)  # pragma: no
   cover` unreachable-guard, the same "defensively unreachable, kept
   for type-checker completeness" convention decision 6 uses.

9. **`TrainingLoadSummary.load` is derived from each session's
   `WorkoutSessionSummary.total_volume` — one of the formulas
   `TrainingLoadRuleContext`'s own module docstring names as legitimate
   ("e.g. session-RPE x duration..., `WorkoutSessionSummary.
   total_volume`, or a wearable-reported training-load metric") — not
   an invented formula.** `CompleteWorkoutSessionHandler` builds this
   by hand because `TrainingLoadRuleContext`, unlike
   `ProgressiveOverloadRuleContext.from_session_contexts()`, declares
   no derivation helper of its own (`docs/adr/0020`: "the application
   layer is responsible for preparing the summaries"). The same handler
   reuses `ProgressiveOverloadRuleContext.from_session_contexts()`
   directly for the overload engine, since that method already performs
   the Completed-only filter and chronological sort this phase needs.

## Consequences

Every multi-aggregate handler in this phase — `StartWorkoutSessionHandler`,
`CompleteWorkoutSessionHandler` — is now the template a future phase
touching more than one aggregate in one transaction should follow: load
each aggregate through its own `uow.get_repository(...)` call, apply
whatever cross-aggregate consistency check neither aggregate alone can
express, mutate each aggregate through its own named methods only,
commit once, then combine and dispatch every aggregate's pulled events
together. A future handler that reaches around this shape — e.g.
mutating one aggregate based on a check that duplicates logic another
aggregate already owns — should be treated as a regression against
decision 4/5, not a stylistic choice.

`list_by_user()` now exists on two repository interfaces with no
persistence behind it, the same gap `docs/adr/0023` left for
`UserPreferences.available_equipment` — a future infrastructure phase
adding concrete `WorkoutRepository`/`WorkoutSessionRepository`
implementations must support an efficient user-scoped list query
alongside `get`/`add`/`remove`.

The Safety/Readiness exclusion in decision 2 is a scope boundary this
phase's own required repository list drew, not a permanent one: a
future phase that adds Safety/Readiness repository access can populate
`ExerciseRecommendationRuleContext`'s remaining optional fields inside
`LogExerciseSetHandler` without changing this handler's overall shape —
the context type was already built to accept them (`docs/adr/0021-
exercise-recommendation-composes-rule-outputs.md`).

The `# pragma: no cover` guards in decisions 6 and 8 will need
revisiting if a future change makes either path reachable (e.g. a new
`Workout.plan()` invariant that can fail on caller-supplied,
not-yet-validated input) — at that point the guard becomes real
behavior with its own test, not defensive dead code, and the pragma
comment should be removed along with the coverage exclusion it
documents.
