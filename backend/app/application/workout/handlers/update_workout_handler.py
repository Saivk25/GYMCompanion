"""`UpdateWorkoutHandler`: replaces a Workout's goal and notes.

Single-aggregate, full-replace, same shape as
`app.application.user.handlers.update_profile_handler`. See
`docs/adr/0024-workout-application-use-cases.md`.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.application.workout.commands.update_workout import UpdateWorkoutCommand
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.repository import WorkoutRepository


class UpdateWorkoutHandler(CommandHandler[UpdateWorkoutCommand, WorkoutId]):
    """Loads a Workout, replaces its goal and notes, and returns the
    same `WorkoutId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher) -> None:
        self._uow = uow
        self._dispatcher = dispatcher

    def handle(self, request: UpdateWorkoutCommand) -> ApplicationResult[WorkoutId]:
        events: Sequence[DomainEvent] = ()
        try:
            with self._uow as uow:
                # WorkoutRepository has no concrete implementation in this phase
                # (by design); mypy's type-abstract check assumes a type[T]
                # argument might be instantiated, but get_repository only ever
                # uses it as a lookup key, so this is a documented, narrow
                # false positive.
                repository = uow.get_repository(
                    WorkoutRepository  # type: ignore[type-abstract]
                )
                workout = repository.get(request.workout_id)
                if workout is None:
                    uow.rollback()
                    return ApplicationResult.fail([f"workout {request.workout_id} not found"])

                workout.update_goal(request.goal)
                workout.update_notes(request.notes)
                uow.commit()
                events = workout.pull_domain_events()
        except DomainInvariantViolationError:
            raise
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(events)
        return ApplicationResult.ok(request.workout_id)
