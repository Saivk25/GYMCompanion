"""`CompleteExerciseSetHandler`: marks one previously logged set
complete within an active WorkoutSession.

Single-aggregate, thin orchestration — `WorkoutSession.complete_set()`
owns every rule about what "complete" means (existence of the
performance, existence of the set number); this handler only loads,
delegates, commits, and dispatches. See
`docs/adr/0024-workout-application-use-cases.md`.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.application.workout.commands.complete_exercise_set import CompleteExerciseSetCommand
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent
from app.domain.workout_session.identifiers import WorkoutSessionId
from app.domain.workout_session.repository import WorkoutSessionRepository


class CompleteExerciseSetHandler(CommandHandler[CompleteExerciseSetCommand, WorkoutSessionId]):
    """Loads a WorkoutSession, marks one logged set complete, and
    returns the same `WorkoutSessionId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: CompleteExerciseSetCommand) -> ApplicationResult[WorkoutSessionId]:
        events: Sequence[DomainEvent] = ()
        try:
            with self._uow as uow:
                # WorkoutSessionRepository has no concrete implementation in
                # this phase (by design); mypy's type-abstract check assumes a
                # type[T] argument might be instantiated, but get_repository
                # only ever uses it as a lookup key, so this is a documented,
                # narrow false positive.
                repository = uow.get_repository(
                    WorkoutSessionRepository  # type: ignore[type-abstract]
                )
                session = repository.get(request.session_id)
                if session is None:
                    uow.rollback()
                    return ApplicationResult.fail(
                        [f"workout session {request.session_id} not found"]
                    )

                session.complete_set(request.performance_id, request.set_number, clock=self._clock)
                uow.commit()
                events = session.pull_domain_events()
        except DomainInvariantViolationError:
            raise
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(events)
        return ApplicationResult.ok(request.session_id)
