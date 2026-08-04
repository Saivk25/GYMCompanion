# ADR 0028: Goal Application Use Cases — why Goal follows Workout's status-lifecycle shape, why the rule engine skips Complete/Cancel, and why `progress` stays `None` here too

- Status: accepted
- Date: 2026-08-05

## Context

Sprint 4's next phase after Readiness (Phase 6, `docs/adr/0027`) is
Goal Application Use Cases: six command/query handlers built on top of
the single `Goal` aggregate (`app.domain.goal`), containing no business
logic of their own, orchestrating `GoalRepository`, `UserRepository`
(when required), a `UnitOfWork`, and `GoalAlignmentRuleEngine`
(`app.domain.goal.rules.goal_alignment_rule_engine`).

This phase begins immediately after TD-0001 (`docs/TECH_DEBT.md`) was
resolved as a standalone, scoped refactor — the duplicated
`_advisory_warnings()` helper is now `app.application.shared.
advisory_warnings.advisory_warnings()`, used by every handler in this
phase from the start; no local copy was ever written here.

`Goal` is structurally different from every aggregate the Application
Layer has exposed so far in one specific way: it has an explicit
four-state lifecycle (`GoalStatus`: `Active`/`Completed`/`Cancelled`/
`Expired`, `goal.py`) with a transition table, the same shape `Workout`
uses (`WorkoutStatus`), not the "no status, a fact captured at a point
in time" shape `Readiness`/`Nutrition`/`Progress` all share. `Goal`'s
four aggregate methods (`create()`, `update()`, `complete()`,
`cancel()`) map directly onto four commands plus two read queries — no
delete command, for the same reason `Workout` has none (decision 2).

`GoalAlignmentRuleContext` (`app.domain.goal.rules.context`) is also
structurally different from every rule context wired into the
Application Layer so far: it references a whole, optional `Progress`
snapshot alongside its required `Goal` snapshot (ADR 0016), the first
rule context in this codebase built specifically to combine two
aggregates. `docs/adr/0026-progress-application-use-cases.md`'s
decision 6 named this phase as the point where a `GoalRepository`
would first exist in the Application Layer, and left its own `goal`
field permanently `None` in every Progress handler for exactly that
reason. This phase does not use that repository's existence as license
to complete the wiring in the other direction — see decision 5.

## Decision

1. **`Goal` remains its own, independent aggregate.** The same
   evidence `docs/adr/0025` decision 1 and `docs/adr/0027` decision 1
   give for `Nutrition`/`Readiness` applies here: `Goal` has its own
   identity, its own repository, and its own consistency boundary; the
   only other aggregate referenced from this phase's handlers,
   `Progress`, is read-only and only ever supplied as an already-loaded
   snapshot to a rule context (and, in this phase, is not even loaded —
   see decision 5), never written through a `Goal` handler. `Goal` is
   referenced by `user_id` only, the same "foreign key, not an
   aggregate reference" discipline every other per-user aggregate
   follows.

2. **No `DeleteGoalCommand`/`DeleteGoalHandler` exists in this
   package.** Unlike Readiness/Nutrition/Progress (all "a fact captured
   at a point in time," hard-deletable via `Repository.remove()` with
   no aggregate method involved — `docs/adr/0027` decision 6), `Goal`
   is a status-lifecycle aggregate: its terminal states are reached by
   `complete()`/`cancel()`, not by deletion. This is the identical
   shape `Workout` already established — `app.application.workout` has
   no `DeleteWorkoutHandler` either, only `CancelWorkoutHandler`. A
   `Goal` a user no longer wants active is cancelled, not erased; its
   record persists as a `Cancelled` goal, the same way a `Workout`
   does.

3. **`CreateGoalCommand`/`UpdateGoalCommand` map one-to-one onto
   `Goal.create()`/`Goal.update()`, not onto individual fields.**
   `Goal.update()` is a single aggregate method covering every mutable
   field at once (`name`, `description`, `target_date`,
   `target_weight`, `target_body_fat`, `target_strength`, `priority`,
   `notes`) — unlike `Readiness`, which exposes three narrower
   `update_*()` methods and accordingly gets three narrower commands
   (`docs/adr/0027` decision 4), `Goal` gets exactly one `UpdateGoalCommand`,
   the identical "one command per aggregate method, not per field"
   shape `UpdateWorkoutCommand` (`docs/adr/0024`) already established.
   `UpdateGoalCommand`'s `None` fields mean "leave unchanged," matching
   `Goal.update()`'s own documented convention, not `UpdateWorkoutCommand`'s
   opposite "clear" convention.

4. **`GoalAlignmentRuleEngine` is invoked from `CreateGoalHandler`/
   `UpdateGoalHandler` only, immediately after a successful `commit()`,
   surfaced solely as `ApplicationResult.warnings` — never a reason to
   fail the command. `CompleteGoalHandler`/`CancelGoalHandler`
   deliberately evaluate no rule engine at all.** Every rule in
   `GoalAlignmentRuleEngine` applies the same guard: "a goal that is not
   `GoalStatus.ACTIVE` always passes, with no recommendation" (ADR
   0016). `complete()`/`cancel()` are precisely the two mutations that
   flip `status` away from `ACTIVE` — re-evaluating immediately
   afterward would therefore always produce an empty `warnings` tuple,
   by construction, for every goal either handler ever touches. This is
   a stronger version of the reasoning `docs/adr/0027`'s
   `UpdateNotesHandler` gives for skipping evaluation on a field no rule
   reads (decision 5 there): here, it isn't one field that's
   rule-irrelevant, it's the specific mutation's own postcondition that
   provably neutralizes every rule in the engine. `CreateGoalHandler`
   always produces an Active goal, and `UpdateGoalHandler` can only
   succeed on a goal that was already Active and stays Active (`update()`
   never changes `status`) — both evaluations are therefore always
   meaningful, unlike Complete/Cancel.

5. **`GoalAlignmentRuleContext.from_aggregates(goal=goal, progress=None,
   clock=...)` — `progress` is deliberately `None`, not a live
   `ProgressRepository.list_by_user()` lookup, even though
   `ProgressRepository` already exists and this phase's handlers could
   technically reach it.** `docs/adr/0026` decision 6 left `Progress`
   handlers' own `goal` field permanently `None`, citing "no
   `GoalRepository` exists in this phase" and naming a future Goal
   Application Use Cases phase as the point that blocker would lift.
   That framing does not, by itself, obligate this phase to wire the
   *other* direction: doing so would leave the two directions
   permanently asymmetric — Goal handlers seeing Progress, Progress
   handlers still not seeing Goal, since editing the already-accepted
   Progress handlers is out of this phase's scope ("do not refactor
   unrelated code"). Two aggregates each partially, asymmetrically aware
   of the other is a worse inconsistency than both staying deliberately
   deferred together. `BodyWeightRule`/`BodyFatRule` — the two rules
   that read `context.progress` — take their own documented "no recent
   body weight/body fat recorded" pass path in every evaluation this
   phase performs, the identical, expected outcome `docs/adr/0026`
   already named for its own mirrored decision. A future phase that
   activates both directions together (updating the already-accepted
   Progress handlers *and* this phase's handlers in the same unit of
   work) is the point this pair of deferred decisions should be
   revisited — not a bug in either phase.

6. **`except DomainInvariantViolationError` is genuinely reachable in
   `UpdateGoalHandler`/`CompleteGoalHandler`/`CancelGoalHandler`, and
   each re-raises it uncaught rather than converting it to a failed
   `ApplicationResult` — the identical choice `UpdateWorkoutHandler`/
   `CancelWorkoutHandler` (`docs/adr/0024`) already make for their own
   reachable `Workout._ensure_mutable()`/transition-table violations.**
   `Goal.update()` calls `_ensure_mutable()`, which raises when the goal
   is not `Active` (e.g. updating an already-Completed goal);
   `complete()`/`cancel()` both call `_transition_to()`, which raises on
   an illegal transition (e.g. completing an already-Cancelled goal).
   Unlike every guard in `docs/adr/0027` decision 7 (all unreachable,
   because `Readiness` has no lifecycle to violate), these three guards
   are exercised by this phase's own tests
   (`test_updating_a_completed_goal_raises_and_still_rolls_back`,
   `test_completing_an_already_completed_goal_raises_and_still_rolls_back`,
   `test_cancelling_a_completed_goal_raises_and_still_rolls_back`), the
   same way `test_cancelling_a_completed_workout_raises_and_still_rolls_back`
   already exercises `CancelWorkoutHandler`'s identical branch. Only
   `CreateGoalHandler`'s guard is unreachable (`Goal.create()`'s only
   invariant, a tz-aware `created_at`, is guaranteed by every `Clock`
   implementation in this codebase) and is marked `# pragma: no cover`
   accordingly, matching every other phase's `Create*Handler`.

7. **`list_by_user(user_id) -> Sequence[Goal]` is added as a new
   abstract method to `GoalRepository`, with no persistence
   implementation** — the identical "declare the contract now, implement
   it in `app.infra` later" split every sibling repository's own
   extension already established (`docs/adr/0024`, `0025`, `0026`,
   `0027`). `ListGoalsHandler` is the concrete caller. The method
   returns every Goal regardless of status — no Active-only filtering
   happens at this layer, matching `GoalRepository`'s own prior "no
   query method grounded in a concrete caller yet" docstring's framing
   of the alternative ("find every Active Goal... ranked by priority")
   as still out of scope; a caller that wants only Active goals filters
   the result itself.

8. **`GoalDTO` is a distinct type from `GoalContext`
   (`app.domain.goal.context`), for the identical reasoning
   `docs/adr/0027` decision 9 gives for `ReadinessDTO` versus
   `ReadinessContext`.** `GoalContext` is scoped to a future domain
   service (Plan generation, NutritionPattern guidance — neither built
   yet), one-directional, and never crosses the Application Layer
   boundary; `GoalDTO` is this layer's own read projection for
   `GetGoalHandler`/`ListGoalsHandler`, a different consumer with
   different reasons to change independently.

## Consequences

This phase's rule-engine wiring is narrower than every prior phase's:
two of four mutating handlers (`CompleteGoalHandler`/
`CancelGoalHandler`) deliberately evaluate nothing, a first in this
codebase. Any future aggregate with its own status-lifecycle rule
engine (none currently planned) should check whether its own terminal
transitions share this same "every rule's guard is trivially satisfied
by the mutation's own postcondition" property before deciding whether
to evaluate at all.

Decision 5 leaves a known, explicitly-named asymmetry in place:
`GoalAlignmentRuleContext.progress` and `ProgressEvaluationRuleContext.
goal` are each permanently `None` from their own respective phase's
handlers, even though both repositories now exist. Neither `BodyWeightRule`/
`BodyFatRule` (Goal Alignment) nor the two Progress rules that read
`context.goal` will ever produce a real cross-aggregate recommendation
until a future unit of work activates both directions deliberately,
together, as its own explicitly scoped task — not as an incidental side
effect of either phase touching its own aggregate's handlers again.
This is a known limitation, not an oversight: recorded here so the next
engineer does not need to re-derive it from reading both ADRs
independently.

`list_by_user()` now exists on `GoalRepository` with no persistence
behind it, matching the same gap left open on every sibling repository
— a future infrastructure phase adding a concrete `GoalRepository`
implementation must support an efficient user-scoped list query
alongside `get`/`add`/`remove`.

No new technical debt was opened by this phase. TD-0001 is closed
(resolved in the prior, standalone refactor); this phase introduces no
duplicated helper of its own, since every rule-relevant handler already
imports the shared `advisory_warnings()`.
