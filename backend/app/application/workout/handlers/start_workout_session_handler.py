"""`StartWorkoutSessionHandler`: begins a new WorkoutSession under an
existing Workout, and advances that Workout's own lifecycle to match.

The clearest example in this phase of "why handlers orchestrate
multiple aggregates" (`docs/adr/0024-workout-application-use-cases.md`):
`Workout` and `WorkoutSession` cannot see each other's state (they are
separate aggregates by design — see that ADR's third topic), so the
cross-aggregate consistency rule "a session cannot start under a
Completed/Cancelled workout" can only be enforced here, in the
Application Layer, the same way `User.delete()`'s own docstring
already reasons about escalation-case checks that no single aggregate
can see on its own.

Advancing the parent `Workout` from Planned to InProgress is
idempotent-forward: if the workout is already InProgress (e.g. a
second session is being started under it), this handler does not call
`workout.start()` again — doing so would raise
`DomainInvariantViolationError` for a case that is not actually
illegal from the caller's point of view ("start another session under
a workout already in progress" is a legitimate action). This is
orchestration bookkeeping, not a reimplementation of `Workout`'s own
transition legality: `Workout._transition_to()` still owns, and is
still the only place that decides, which transitions are legal at all.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.application.workout.commands.start_workout_session import StartWorkoutSessionCommand
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent
from app.domain.workout.enums import WorkoutStatus
from app.domain.workout.repository import WorkoutRepository
from app.domain.workout_session.identifiers import WorkoutSessionId
from app.domain.workout_session.repository import WorkoutSessionRepository
from app.domain.workout_session.workout_session import WorkoutSession

_BLOCKED_STATUSES = (WorkoutStatus.COMPLETED, WorkoutStatus.CANCELLED)


class StartWorkoutSessionHandler(CommandHandler[StartWorkoutSessionCommand, WorkoutSessionId]):
    """Loads the parent Workout, starts a new WorkoutSession under it,
    conditionally advances the Workout to InProgress, and returns the
    new `WorkoutSessionId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: StartWorkoutSessionCommand) -> ApplicationResult[WorkoutSessionId]:
        session_id = WorkoutSessionId.generate()
        events: Sequence[DomainEvent] = ()

        try:
            with self._uow as uow:
                # WorkoutRepository/WorkoutSessionRepository have no concrete
                # implementation in this phase (by design); mypy's type-abstract
                # check assumes a type[T] argument might be instantiated, but
                # get_repository only ever uses it as a lookup key — a
                # documented, narrow false positive, the same one every prior
                # handler in this codebase already carries.
                workout_repository = uow.get_repository(
                    WorkoutRepository  # type: ignore[type-abstract]
                )
                workout = workout_repository.get(request.workout_id)
                if workout is None:
                    uow.rollback()
                    return ApplicationResult.fail([f"workout {request.workout_id} not found"])

                if workout.status in _BLOCKED_STATUSES:
                    uow.rollback()
                    return ApplicationResult.fail(
                        [f"cannot start a session for a workout in status {workout.status.value!r}"]
                    )

                session = WorkoutSession.plan(
                    session_id=session_id,
                    workout_id=workout.id,
                    user_id=workout.user_id,
                    session_date=request.session_date,
                    clock=self._clock,
                )
                session.start(clock=self._clock)

                if workout.status is WorkoutStatus.PLANNED:
                    workout.start(clock=self._clock)

                session_repository = uow.get_repository(
                    WorkoutSessionRepository  # type: ignore[type-abstract]
                )
                session_repository.add(session)
                uow.commit()
                events = (*workout.pull_domain_events(), *session.pull_domain_events())
        except DomainInvariantViolationError:
            # Currently unreachable: this handler already checks
            # `workout.status` before calling `session.start()`/
            # `workout.start()`, so neither call can hit an illegal
            # transition on any path reaching this line. Kept anyway for
            # defensive consistency with every other mutating handler's
            # "always re-raise, never convert" policy — see the module
            # docstring.
            raise  # pragma: no cover
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(events)
        return ApplicationResult.ok(session_id)
