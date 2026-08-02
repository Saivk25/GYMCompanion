# ADR 0026: Progress Application Use Cases — why ProgressEvaluationRuleEngine is advisory, why handlers never calculate trends, and why analytics remain outside the Application Layer

- Status: accepted
- Date: 2026-08-02

## Context

Sprint 4, Phase 5 asked for the fourth concrete consumer of the
Application Layer Foundation (`docs/adr/0022-application-layer-
foundation.md`): seven command/query handlers built on top of the
single `Progress` aggregate (`app.domain.progress`), containing "NO
business logic" of their own, orchestrating `ProgressRepository`,
`UserRepository` (when required), a `UnitOfWork`, and
`ProgressEvaluationRuleEngine`
(`app.domain.progress.rules.progress_evaluation_rule_engine`). The task
named a fixed file list (five commands, two queries, one DTO, seven
handlers) and three required ADR topics: why
`ProgressEvaluationRuleEngine` recommendations are advisory, why
handlers never calculate trends, and why analytics remain outside the
Application Layer.

Unlike Sprint 4, Phase 4 (`docs/adr/0025-nutrition-application-use-
cases.md`), where `NutritionRuleContext.from_nutrition()` builds
directly off the just-mutated aggregate with no history dependency,
`ProgressEvaluationRuleContext` combines an ordered *history* of
`ProgressContext` snapshots with an optional `GoalContext` reference
(that context type's own module docstring) — three of its five rules
(`ConsistencyRule`, `MeasurementTrendRule`, `PlateauRule`) are
inherently about trends across many check-ins, not one record in
isolation, and two (`BodyWeightRule`, `BodyFatRule`) compare the
history against an active Goal's target. This makes Progress's
rule-engine integration structurally closer to Sprint 4, Phase 3's
`CompleteWorkoutSessionHandler` (`docs/adr/0024-workout-application-
use-cases.md`, decision 3) than to Nutrition's simpler shape: every
mutating handler that evaluates the engine must first rebuild the
user's full check-in history via `ProgressRepository.list_by_user()`
(added this phase, following the same precedent), not just read the
one aggregate it just touched.

One structural gap existed before `ListProgressHandler` — and every
rule-engine-evaluating handler — could be written:
`ProgressRepository` declared nothing beyond `get`/`add`/`remove`, and
this module's own prior docstring had already anticipated the
extension ("no query method here... is grounded in a concrete caller
in this codebase yet") — this phase is that concrete caller, following
the identical precedent `docs/adr/0024` and `docs/adr/0025` already
established for `WorkoutRepository`/`WorkoutSessionRepository`/
`NutritionRepository`.

## Decision

1. **`ProgressEvaluationRuleEngine` is invoked from the Application
   Layer, immediately after a successful `commit()`, and its output is
   surfaced only as `ApplicationResult.warnings` — never a reason to
   fail the command.** This mirrors the "evaluation-only, cannot itself
   block" discipline every rule engine wired into this codebase already
   documents for itself (`docs/adr/0018-safety-rule-engine-composition-
   and-authority.md`, `docs/adr/0024`, `docs/adr/0025`) — a rule engine
   evaluates deterministically over a `RuleContext` and returns
   recommendations; it never has the authority to reject a command, and
   this phase's task explicitly says so ("Never fail because of
   recommendations"). Concretely: if `ConsistencyRule` flags a
   brand-new user's first-ever check-in as having too few entries for
   meaningful evaluation, `RecordProgressHandler` still returns
   `ApplicationResult.ok(...)` with the warning attached — the check-in
   was still recorded exactly as the caller asked; the warning is
   advice about the *evaluation*, not a correction to the *record*.
   This is the same posture `docs/adr/0025`, decision 2 establishes for
   `NutritionRuleEngine`, applied to a history-based engine instead of
   a single-record one. The small `_advisory_warnings(result:
   RuleResult) -> tuple[str, ...]` helper is duplicated in each
   rule-evaluating handler file rather than factored into a shared
   module, the identical "two call sites sharing one three-line
   function is not yet the second real need" reasoning `docs/adr/0024`
   and `docs/adr/0025` give for their own identical helpers.

2. **Handlers in this package never calculate a trend, streak, or
   personal record — every body-composition/measurement value a
   handler touches is a value the caller supplied (via a `Command`) or
   a value already stored on an aggregate, never a derived one; the
   only "computation" any handler performs is assembling a
   `ProgressEvaluationRuleContext` from already-loaded aggregates and
   handing it to the engine, not computing the trend itself.**
   `RecordProgressHandler`/`UpdateBodyCompositionHandler`/
   `UpdateMeasurementsHandler` all call
   `ProgressEvaluationRuleContext.from_aggregates(progress_records=
   history, goal=None, clock=self._clock)` — `from_aggregates()` itself
   only snapshots each `Progress` via `ProgressContext.from_progress()`
   and sorts chronologically (`from_snapshots()`'s own docstring); the
   actual slope/regression/plateau-detection logic lives entirely
   inside `MeasurementTrendRule`/`PlateauRule` in the Domain Layer,
   deterministic and framework-independent, exactly where
   `docs/adr/0013-rule-engine-foundation.md` puts it. This is inherited
   directly from `Progress`'s own scope decision (`progress.py`'s
   module docstring): "This aggregate stores canonical progress
   information only. It does not compute trends, streaks, personal
   records, or anything derived from a series of records — that is
   Progress Intelligence's job... a separate, not-yet-built context." A
   handler orchestrating `Progress` cannot introduce computation both
   the aggregate and this phase's rule engine were deliberately scoped
   to exclude — doing so would silently relocate business logic out of
   the layer that owns it. "Analytics", "Charts", and "Trend
   calculations" are named in this phase's own "Do NOT implement" list
   for the same reason: they are the class of computation this scope
   boundary exists to keep out.

3. **Analytics — charts, dashboards, computed trend lines, forecasts —
   remain entirely outside the Application Layer, not merely
   unimplemented in this package specifically.** The Application
   Layer's own stated job (`docs/adr/0022`) is orchestration:
   sequencing repository/`UnitOfWork`/rule-engine calls, never deciding
   what those calls mean. `ProgressEvaluationRuleEngine` already
   represents the full extent of deterministic, rule-based evaluation
   this codebase performs over Progress history — Bible Section 8,
   Table 40's own layering ("Rule Layer... Statistical Layer... AI
   Advisory Layer", quoted in `ProgressEvaluationRuleContext`'s own
   module docstring) places the actual statistical regression behind a
   real `Trend`/`Forecast` entity in a Statistical Layer this codebase
   has not built, deliberately out of scope for an Application Layer
   whose only job is to invoke Domain Layer rules and repositories.
   Building a chart, a computed streak, or a forecast would require
   either duplicating logic that belongs in a not-yet-built Progress
   Intelligence context, or inventing new business logic inside a
   handler — both of which this phase's "Handlers contain NO business
   logic" instruction and its own "Do NOT implement" list rule out.
   Nothing about *this* phase's package boundary is different from
   `docs/adr/0025`'s equivalent scope line for Nutrition ("meal
   planning... macro optimization... food database"); the pattern is
   the same discipline applied to a different aggregate's future
   Intelligence layer.

4. **`UpdateBodyCompositionCommand`/`UpdateMeasurementsCommand`'s
   `None` fields mean "leave unchanged" — the same convention
   `Progress.update_body_composition()`/`Progress.
   update_measurements()` themselves already document — not "clear,"
   which is the opposite convention `UpdateWorkoutCommand`
   (`docs/adr/0024`) uses for `Workout`'s `goal`/`notes`.** This is the
   identical reasoning `docs/adr/0025`, decision 4 establishes for
   `UpdateNutritionCommand`: a command's job is to carry caller intent
   through to the aggregate method unmodified, and both aggregate
   methods already define what their own `None` arguments mean before
   this phase existed. `UpdateNotesCommand`, by contrast, makes `notes`
   a required field, matching `Progress.update_notes(notes:
   ProgressNotes, ...)` taking no optional/"leave unchanged" form —
   there is nothing to leave unchanged in a single-field wholesale
   replace, the same shape `UpdateWaterCommand` (`docs/adr/0025`)
   establishes for `Nutrition.update_water()`.

5. **Only three of this phase's five mutating handlers evaluate
   `ProgressEvaluationRuleEngine` — `RecordProgressHandler`,
   `UpdateBodyCompositionHandler`, `UpdateMeasurementsHandler`.
   `UpdateNotesHandler` and `DeleteProgressHandler` do not, on the same
   "rule-relevant fields only" scope `docs/adr/0025` draws for which
   Nutrition handlers wire in `NutritionRuleEngine`.** None of this
   engine's five rules (`BodyWeightRule`, `BodyFatRule`,
   `MeasurementTrendRule`, `ConsistencyRule`, `PlateauRule`) reads
   `Progress.notes` — re-evaluating after a notes-only change would
   produce a result identical to whatever the last rule-relevant
   mutation already produced, at the cost of an extra
   `list_by_user()` call for no new information. `DeleteProgressHandler`
   calls `ProgressRepository.remove()` directly, not an aggregate
   method — `Progress` has no delete/soft-delete method and raises no
   `ProgressDeleted` event (`events.py` is scoped to exactly the four
   events `record()`/`update_body_composition()`/`update_measurements()`/
   `update_notes()` raise) — and evaluates no rule engine either, the
   identical reasoning `DeleteNutritionHandler` (`docs/adr/0025`)
   documents: deletion removes the very record the engine would
   evaluate. `DeleteProgressHandler` still dispatches an empty event
   tuple unconditionally on every success, since
   `DomainEventDispatcher.dispatch(())` is explicitly a well-defined
   no-op and there is nothing to lose by calling it uniformly with
   every other handler in this package.

6. **Every rule-evaluating handler builds its
   `ProgressEvaluationRuleContext` from the user's *full* check-in
   history via `ProgressRepository.list_by_user()`, called after
   `uow.commit()` but still inside the same `with self._uow as uow`
   block — the identical ordering `CompleteWorkoutSessionHandler`
   (`docs/adr/0024`, decision 3) establishes for its own trend-based
   engines.** `ConsistencyRule`/`MeasurementTrendRule`/`PlateauRule` are
   inherently about trends across many check-ins; evaluating only the
   one record a handler just touched would make three of the engine's
   five rules trivially unable to fire meaningfully (e.g.
   `ConsistencyRule`'s minimum-3-entries threshold could never be
   satisfied by a single-record context). `goal` is always `None` in
   every call this phase makes: no `GoalRepository` exists in this
   phase's required repository list (`ProgressRepository`,
   `UserRepository`, `UnitOfWork`, `ProgressEvaluationRuleEngine` only)
   — Goal Application Use Cases are explicitly a later phase, named in
   this phase's own "Do NOT implement" list. `BodyWeightRule`/
   `BodyFatRule` — the two rules that read `context.goal` — therefore
   always take their own documented "no active goal supplied, cannot
   evaluate" pass path in this phase; a future Goal Application Use
   Cases phase that adds `GoalRepository` access can populate `goal`
   without changing any handler's overall shape, the same "context type
   already has room for it" forward-compatibility `docs/adr/0024`,
   decision 2 notes for `ExerciseRecommendationRuleContext`.

7. **`RecordProgressHandler`'s, `UpdateBodyCompositionHandler`'s, and
   `UpdateMeasurementsHandler`'s `except DomainInvariantViolationError:
   raise` guards are currently unreachable — kept for defensive
   consistency with every other mutating handler's "always re-raise,
   never convert" policy (`docs/adr/0023`, decision 3; `docs/adr/0024`,
   decision 6; `docs/adr/0025`, decision 6), not because any of the
   three paths is reachable today.** `Progress` has "no status enum and
   no lifecycle" (`progress.py`'s own module docstring) — none of
   `record()`, `update_body_composition()`, or `update_measurements()`
   guards a state transition the way `Workout._transition_to()` does,
   and `record()`'s only invariant (`ensure(recorded_at.tzinfo is not
   None, ...)`) is guaranteed by every `Clock` implementation in this
   codebase. All three guards are marked `# pragma: no cover` with an
   explanatory comment, the same convention `docs/adr/0024`/
   `docs/adr/0025` established for their own currently-unreachable
   guards. `UpdateNotesHandler` carries the identical guard for the
   identical reason (`update_notes()` also raises no
   `DomainInvariantViolationError`); `DeleteProgressHandler` invokes no
   aggregate method at all and so carries no such guard, the same
   omission `docs/adr/0025` notes for `DeleteNutritionHandler`.

8. **`list_by_user(user_id) -> Sequence[Progress]` is added as a new
   abstract method to `ProgressRepository`, with no persistence
   implementation** — the identical "declare the contract now,
   implement it in `app.infra` later" split `docs/adr/0024`/
   `docs/adr/0025` established for `WorkoutRepository`/
   `WorkoutSessionRepository`/`NutritionRepository`. `ListProgressHandler`
   is the direct-listing caller; every rule-evaluating handler
   (decision 6) is the history-building caller. The method promises no
   ordering — it returns every record for a user, unfiltered; a caller
   needing a specific order (e.g. chronological) sorts the result
   itself, matching `ProgressEvaluationRuleContext.from_snapshots()`'s
   own chronological sort as the concrete example of a caller that
   does exactly this.

9. **`ProgressDTO` is a distinct type from `ProgressContext`
   (`app.domain.progress.context`), for the identical reasoning
   `docs/adr/0023`/`docs/adr/0024`/`docs/adr/0025` give for `UserDTO`/
   `WorkoutDTO`/`NutritionDTO` versus their own `*Context` types.**
   `ProgressContext` is scoped to `ProgressEvaluationRuleEngine` (and
   any future Progress Intelligence trend/plateau/forecast computation,
   not built yet), one-directional, and never crosses the Application
   Layer boundary; `ProgressDTO` is this layer's own read projection
   for `GetProgressHandler`/`ListProgressHandler`, a different consumer
   with different reasons to change independently.

## Consequences

Every rule-evaluating handler in this phase pays the cost of an extra
`list_by_user()` call after every mutation — proportional to a user's
full check-in history, not the single record being touched. This is a
deliberate trade consistent with `CompleteWorkoutSessionHandler`'s
identical cost (`docs/adr/0024`): correctness of a trend-based
evaluation requires the trend's actual data, and no cheaper
approximation was available within this phase's own repository
contract. A future infrastructure phase implementing
`ProgressRepository.list_by_user()` against Postgres should expect this
call pattern (called once per mutating command, not once per page
load) when sizing indexes/query plans.

`goal` being permanently `None` in this phase (decision 6) means
`BodyWeightRule`/`BodyFatRule` are currently dead weight in every
evaluation this phase's handlers perform — they always pass via their
"no active goal supplied" branch. This is expected and not a bug: those
two rules exist for a future Goal Application Use Cases phase to
activate by supplying real `GoalContext` data, not for this phase to
exercise meaningfully. That future phase should be the one to revisit
this decision, passing a real `goal` value once `GoalRepository`
becomes part of some handler's dependency list.

The `# pragma: no cover` guards in decision 7 will need revisiting if a
future change gives `Progress` an invariant that can fail on
caller-supplied input (e.g. a future business rule constraining which
fields can be updated together, or a lifecycle concept this increment
deliberately did not build — see `docs/adr/0010-progress-immutability-
is-a-policy-not-a-guard.md`) — at that point the guard becomes real
behavior with its own test, and the pragma comment should be removed
along with the coverage exclusion it documents.
