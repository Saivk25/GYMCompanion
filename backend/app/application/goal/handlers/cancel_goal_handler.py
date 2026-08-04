"""`CancelGoalHandler`: cancels an Active Goal.

Single-aggregate, same shape as `app.application.workout.handlers.
cancel_workout_handler.CancelWorkoutHandler`: `DomainInvariantViolationError`
is genuinely reachable here (cancelling an already-Completed or
-Cancelled goal) and is re-raised uncaught rather than converted to a
failed `ApplicationResult` — the same choice that handler documents for
its own reachable transition guard.

No `GoalAlignmentRuleEngine` evaluation here — see
`CompleteGoalHandler`'s own docstring for the full reasoning, which
applies identically: `cancel()` is the other mutation that flips
`status` away from `ACTIVE`, so every rule in this engine would
trivially pass with no recommendation if re-evaluated after this call.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.goal.commands.cancel_goal import CancelGoalCommand
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.goal.identifiers import GoalId
from app.domain.goal.repository import GoalRepository
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent


class CancelGoalHandler(CommandHandler[CancelGoalCommand, GoalId]):
    """Loads a Goal, cancels it, and returns the same `GoalId` on
    success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: CancelGoalCommand) -> ApplicationResult[GoalId]:
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

                goal.cancel(clock=self._clock)
                uow.commit()
                events = goal.pull_domain_events()
        except DomainInvariantViolationError:
            raise
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(events)
        return ApplicationResult.ok(request.goal_id)
