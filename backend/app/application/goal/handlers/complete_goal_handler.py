"""`CompleteGoalHandler`: marks an Active Goal as Completed.

Single-aggregate, same shape as `app.application.workout.handlers.
cancel_workout_handler.CancelWorkoutHandler`: `DomainInvariantViolationError`
is genuinely reachable here (completing an already-Completed or
-Cancelled goal) and is re-raised uncaught rather than converted to a
failed `ApplicationResult` — the same choice that handler documents for
its own reachable transition guard.

No `GoalAlignmentRuleEngine` evaluation here, unlike `CreateGoalHandler`/
`UpdateGoalHandler`. Every rule in this engine applies the same guard —
"a goal that is not `GoalStatus.ACTIVE` always passes, with no
recommendation" (`docs/adr/0016-goal-alignment-combines-whole-snapshots.
md`) — and `complete()` is precisely the mutation that flips `status`
away from `ACTIVE`. Re-evaluating after this call would therefore always
produce an empty `warnings` tuple, by construction, for every goal this
handler ever touches — the same "re-evaluating provably cannot change
the outcome, so skip it and document why" reasoning `UpdateNotesHandler`
(`app.application.readiness.handlers.update_notes_handler`) applies for
a different reason (a field no rule reads, rather than a status guard
every rule shares). See `docs/adr/0028-goal-application-use-cases.md`.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.goal.commands.complete_goal import CompleteGoalCommand
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.ownership import ensure_owner
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.goal.identifiers import GoalId
from app.domain.goal.repository import GoalRepository
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent


class CompleteGoalHandler(CommandHandler[CompleteGoalCommand, GoalId]):
    """Loads a Goal, marks it Completed, and returns the same `GoalId`
    on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: CompleteGoalCommand) -> ApplicationResult[GoalId]:
        events: Sequence[DomainEvent] = ()

        try:
            with self._uow as uow:
                # GoalRepository has no concrete implementation in this
                # phase (by design); mypy's type-abstract check assumes a
                # type[T] argument might be instantiated, but get_repository
                # only ever uses it as a lookup key, so this is a documented,
                # narrow false positive.
                repository = uow.get_repository(GoalRepository)  # type: ignore[type-abstract]
                goal = repository.get(request.goal_id)
                if goal is None:
                    uow.rollback()
                    return ApplicationResult.fail([f"goal {request.goal_id} not found"])

                denial = ensure_owner(owner_id=goal.user_id, requester_id=request.requester_id)
                if denial is not None:
                    uow.rollback()
                    return ApplicationResult.forbid([denial])

                goal.complete(clock=self._clock)
                uow.commit()
                events = goal.pull_domain_events()
        except DomainInvariantViolationError:
            raise
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(events)
        return ApplicationResult.ok(request.goal_id)
