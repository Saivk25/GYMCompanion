"""The Goal Application Use Cases — Sprint 4's next phase after Readiness.

Coordinates the `Goal` aggregate (`app.domain.goal`) with repository
interfaces and a `UnitOfWork` (both from `app.application.shared`),
containing no business rules of its own: every decision about what
makes a Goal valid lives on `Goal`/its value objects themselves. This
package only sequences calls — load (or check user existence), mutate,
commit, dispatch, evaluate — the same orchestration-not-decision
boundary `docs/adr/0022-application-layer-foundation.md` establishes for
the Application Layer generally. See `docs/adr/0028-goal-application-
use-cases.md` for the decisions specific to this phase.

Four subpackages, one per concern, mirroring `app.application.readiness`/
`app.application.progress`'s own layout:

- `commands/`: immutable write-intent inputs (`CreateGoalCommand`,
  `UpdateGoalCommand`, `CompleteGoalCommand`, `CancelGoalCommand`).
- `queries/`: immutable read-intent inputs (`GetGoalQuery`,
  `ListGoalsQuery`).
- `dto/`: `GoalDTO`, the read-only shape a query handler returns.
- `handlers/`: the `CommandHandler`/`QueryHandler` implementations
  that actually orchestrate, including `GoalAlignmentRuleEngine` —
  invoked after a successful commit on `CreateGoalHandler`/
  `UpdateGoalHandler` only, surfaced solely as advisory
  `ApplicationResult.warnings`, never a reason to fail a command.

No hard-delete use case exists here, unlike Readiness/Nutrition/
Progress — `Goal` is a status-lifecycle aggregate (`Active` ->
`Completed`/`Cancelled`, the same shape `Workout` uses), not a
check-in, so `CompleteGoalHandler`/`CancelGoalHandler` are this
package's terminal operations, matching `app.application.workout`
having no `DeleteWorkoutHandler` either. No concrete repository, no
SQLAlchemy, no FastAPI, and no AI integration exists in this package —
see the ADR for what's deliberately out of scope.
"""
