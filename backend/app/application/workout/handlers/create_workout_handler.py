"""`CreateWorkoutHandler`: plans a brand-new Workout for an existing
User.

Orchestrates two repositories (`UserRepository`, `WorkoutRepository`)
within one `UnitOfWork` — the existence check against `UserRepository`
is a referential-integrity check ("does this user exist"), not a
business rule; every decision about what makes a `Workout` valid still
lives on `Workout` itself. See
`docs/adr/0024-workout-application-use-cases.md`.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.application.workout.commands.create_workout import CreateWorkoutCommand
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.repository import UserRepository
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.repository import WorkoutRepository
from app.domain.workout.workout import Workout


class CreateWorkoutHandler(CommandHandler[CreateWorkoutCommand, WorkoutId]):
    """Plans a new Workout and returns its freshly generated
    `WorkoutId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: CreateWorkoutCommand) -> ApplicationResult[WorkoutId]:
        workout_id = WorkoutId.generate()
        events: Sequence[DomainEvent] = ()

        try:
            with self._uow as uow:
                # UserRepository/WorkoutRepository have no concrete implementation
                # in this phase (by design); mypy's type-abstract check assumes a
                # type[T] argument might be instantiated, but get_repository only
                # ever uses it as a lookup key — a documented, narrow false
                # positive, the same one every User Application handler already
                # carries (see app/application/user/handlers/).
                user_repository = uow.get_repository(UserRepository)  # type: ignore[type-abstract]
                user = user_repository.get(request.user_id)
                if user is None:
                    uow.rollback()
                    return ApplicationResult.fail([f"user {request.user_id} not found"])

                workout = Workout.plan(
                    workout_id=workout_id,
                    user_id=request.user_id,
                    name=request.name,
                    planned_date=request.planned_date,
                    goal=request.goal,
                    notes=request.notes,
                    clock=self._clock,
                )
                workout_repository = uow.get_repository(
                    WorkoutRepository  # type: ignore[type-abstract]
                )
                workout_repository.add(workout)
                uow.commit()
                events = workout.pull_domain_events()
        except DomainInvariantViolationError:
            # Currently unreachable: `Workout.plan()`'s own invariant
            # (a tz-aware `planned_at`) is guaranteed by every `Clock`
            # implementation in this codebase, and every other field is a
            # value object already validated at construction, before this
            # handler ever runs. Kept anyway for defensive consistency with
            # every other mutating handler's "always re-raise, never
            # convert" policy — see the module docstring.
            raise  # pragma: no cover
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(events)
        return ApplicationResult.ok(workout_id)
