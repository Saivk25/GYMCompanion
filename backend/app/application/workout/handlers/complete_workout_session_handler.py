"""`CompleteWorkoutSessionHandler`: completes an active WorkoutSession,
advances its parent Workout to match, and surfaces
`ProgressiveOverloadRuleEngine`/`TrainingLoadRuleEngine` advice as
warnings.

The second, richer example of "why handlers orchestrate multiple
aggregates" (`docs/adr/0024-workout-application-use-cases.md`,
alongside `StartWorkoutSessionHandler`): completing the session and
conditionally completing its parent Workout (idempotent-forward, same
reasoning as `StartWorkoutSessionHandler`) both happen in one
transaction, because no single aggregate can see both sides of "this
was the workout's last active session."

Builds `ProgressiveOverloadRuleContext` and `TrainingLoadRuleContext`
from the user's full session history
(`WorkoutSessionRepository.list_by_user()`), because both engines are
inherently about trends across many sessions, not just the one being
completed here — this is the "historical summaries already supplied by
the application layer" role both context types' own module docstrings
describe. `ProgressiveOverloadRuleContext.from_session_contexts()` does
its own Completed-only filtering and chronological sort; this handler
does the same filtering manually for `TrainingLoadRuleContext`, since
that context (per its own module docstring and
`docs/adr/0020-training-load-supplied-summaries.md`) declares no
derivation helper of its own — "the application layer is responsible
for preparing the summaries." `TrainingLoadSummary.load` reuses each
session's `WorkoutSessionSummary.total_volume` as the load scalar, one
of the formulas `TrainingLoadRuleContext`'s own module docstring names
as legitimate.

Both engines are evaluation-only and cannot fail this workflow; their
combined `recommendations` are surfaced as `ApplicationResult.warnings`.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.shared.advisory_warnings import advisory_warnings
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.application.workout.commands.complete_workout_session import (
    CompleteWorkoutSessionCommand,
)
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent
from app.domain.training_load.rules.context import (
    TrainingLoad,
    TrainingLoadDate,
    TrainingLoadRuleContext,
    TrainingLoadSummary,
)
from app.domain.training_load.rules.training_load_rule_engine import TrainingLoadRuleEngine
from app.domain.workout.enums import WorkoutStatus
from app.domain.workout.repository import WorkoutRepository
from app.domain.workout.rules.context import ProgressiveOverloadRuleContext, WorkoutSessionSummary
from app.domain.workout.rules.progressive_overload_rule_engine import (
    ProgressiveOverloadRuleEngine,
)
from app.domain.workout.value_objects import WorkoutDuration
from app.domain.workout_session.context import WorkoutSessionContext
from app.domain.workout_session.enums import SessionStatus
from app.domain.workout_session.identifiers import WorkoutSessionId
from app.domain.workout_session.repository import WorkoutSessionRepository

_overload_engine = ProgressiveOverloadRuleEngine()
_training_load_engine = TrainingLoadRuleEngine()


class CompleteWorkoutSessionHandler(
    CommandHandler[CompleteWorkoutSessionCommand, WorkoutSessionId]
):
    """Completes a WorkoutSession, conditionally completes its parent
    Workout, and returns the same `WorkoutSessionId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: CompleteWorkoutSessionCommand) -> ApplicationResult[WorkoutSessionId]:
        events: Sequence[DomainEvent] = ()
        warnings: tuple[str, ...] = ()

        try:
            with self._uow as uow:
                # WorkoutSessionRepository/WorkoutRepository have no concrete
                # implementation in this phase (by design); mypy's type-abstract
                # check assumes a type[T] argument might be instantiated, but
                # get_repository only ever uses it as a lookup key — a
                # documented, narrow false positive, the same one every prior
                # handler in this codebase already carries.
                session_repository = uow.get_repository(
                    WorkoutSessionRepository  # type: ignore[type-abstract]
                )
                session = session_repository.get(request.session_id)
                if session is None:
                    uow.rollback()
                    return ApplicationResult.fail(
                        [f"workout session {request.session_id} not found"]
                    )

                session.complete(
                    duration=request.duration,
                    completion_percentage=request.completion_percentage,
                    rating=request.rating,
                    clock=self._clock,
                )

                workout_repository = uow.get_repository(
                    WorkoutRepository  # type: ignore[type-abstract]
                )
                workout = workout_repository.get(session.workout_id)
                if workout is None:
                    uow.rollback()
                    return ApplicationResult.fail([f"workout {session.workout_id} not found"])

                if workout.status is WorkoutStatus.IN_PROGRESS:
                    workout.complete(
                        duration=WorkoutDuration(value=request.duration.value),
                        clock=self._clock,
                    )

                uow.commit()
                events = (*session.pull_domain_events(), *workout.pull_domain_events())

                history = session_repository.list_by_user(session.user_id)
                session_contexts = tuple(
                    WorkoutSessionContext.from_workout_session(historical_session)
                    for historical_session in history
                )

                overload_context = ProgressiveOverloadRuleContext.from_session_contexts(
                    session_contexts
                )
                overload_result = _overload_engine.evaluate(overload_context)

                training_load_summaries = tuple(
                    TrainingLoadSummary(
                        load_date=TrainingLoadDate(value=summary.session_date.value),
                        load=TrainingLoad(value=summary.total_volume),
                    )
                    for summary in (
                        WorkoutSessionSummary.from_session_context(context)
                        for context in session_contexts
                        if context.status is SessionStatus.COMPLETED
                    )
                )
                training_load_context = TrainingLoadRuleContext.from_summaries(
                    training_load_summaries
                )
                training_load_result = _training_load_engine.evaluate(training_load_context)

                warnings = advisory_warnings(overload_result) + advisory_warnings(
                    training_load_result
                )
        except DomainInvariantViolationError:
            raise
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(events)
        return ApplicationResult.ok(request.session_id, warnings=warnings)
