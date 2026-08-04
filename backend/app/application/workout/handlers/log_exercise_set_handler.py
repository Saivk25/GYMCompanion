"""`LogExerciseSetHandler`: logs one set of one exercise within an
active WorkoutSession, and surfaces `ExerciseRecommendationRuleEngine`
advice as warnings.

Orchestrates `WorkoutSessionRepository` and `ExerciseRepository`
(lookup only — see `LogExerciseSetCommand`'s own docstring on the
"typed reference in, existence checked by the caller" split of
responsibility). "Find or create" the `ExercisePerformance` for
`exercise_id` is application-level bookkeeping, not business logic:
the actual legality of adding an exercise to this session is still
enforced entirely by `WorkoutSession.add_exercise()`'s own
`_ensure_mutable()` guard, this handler only decides *which* existing
performance (if any) to reuse.

`ExerciseRecommendationRuleEngine` is invoked with a minimal context —
only the required `exercise: ExerciseContext` field is populated; every
other field (`goal`, `safety_result`, `readiness_result`,
`progressive_overload`, `declared_restrictions`, `available_equipment`,
`recent_movement_patterns`) is left at its documented default because
no Goal/Safety/Readiness repository access is available to this
handler — see `docs/adr/0024-workout-application-use-cases.md`'s scope
note. The engine is evaluation-only and can never fail this workflow
(`ExerciseRecommendationRuleEngine`'s own class docstring); its
`recommendations` are surfaced as `ApplicationResult.warnings`.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.shared.advisory_warnings import advisory_warnings
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.application.workout.commands.log_exercise_set import LogExerciseSetCommand
from app.domain.exercise.context import ExerciseContext
from app.domain.exercise.repository import ExerciseRepository
from app.domain.exercise.rules.context import ExerciseRecommendationRuleContext
from app.domain.exercise.rules.exercise_recommendation_rule_engine import (
    ExerciseRecommendationRuleEngine,
)
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent
from app.domain.workout_session.exercise_set import ExerciseSet
from app.domain.workout_session.identifiers import ExercisePerformanceId
from app.domain.workout_session.repository import WorkoutSessionRepository

_recommendation_engine = ExerciseRecommendationRuleEngine()


class LogExerciseSetHandler(CommandHandler[LogExerciseSetCommand, ExercisePerformanceId]):
    """Logs one set within a session, finding or creating the matching
    `ExercisePerformance`, and returns its `ExercisePerformanceId` on
    success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: LogExerciseSetCommand) -> ApplicationResult[ExercisePerformanceId]:
        # `performance_id` has no safe trivial default (unlike `events`/
        # `warnings`, which can default to `()`); it is only ever assigned
        # inside the `try` below. The `AssertionError` guard after the
        # `try`/`except` documents that every non-exception, non-early-
        # return path above does assign it — mirroring this codebase's
        # existing `# pragma: no cover — abstract, always overridden`
        # convention for defensively unreachable code.
        performance_id: ExercisePerformanceId | None = None
        warnings: tuple[str, ...] = ()
        events: Sequence[DomainEvent] = ()

        try:
            with self._uow as uow:
                # WorkoutSessionRepository/ExerciseRepository have no concrete
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

                exercise_repository = uow.get_repository(
                    ExerciseRepository  # type: ignore[type-abstract]
                )
                exercise = exercise_repository.get(request.exercise_id)
                if exercise is None:
                    uow.rollback()
                    return ApplicationResult.fail([f"exercise {request.exercise_id} not found"])

                existing_performance = next(
                    (
                        performance
                        for performance in session.exercise_performances
                        if performance.exercise_id == request.exercise_id
                    ),
                    None,
                )
                if existing_performance is not None:
                    performance_id = existing_performance.id
                else:
                    performance_id = session.add_exercise(request.exercise_id, clock=self._clock)

                exercise_set = ExerciseSet(
                    set_number=request.set_number,
                    weight=request.weight,
                    reps=request.reps,
                    rpe=request.rpe,
                )
                session.log_set(performance_id, exercise_set, clock=self._clock)
                uow.commit()
                events = session.pull_domain_events()

                recommendation_context = ExerciseRecommendationRuleContext(
                    exercise=ExerciseContext.from_exercise(exercise)
                )
                rule_result = _recommendation_engine.evaluate(recommendation_context)
                warnings = advisory_warnings(rule_result)
        except DomainInvariantViolationError:
            raise
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        if performance_id is None:
            raise AssertionError(  # pragma: no cover — unreachable: every
                # non-exception, non-early-return path above assigns
                # performance_id before reaching here.
                "performance_id must be assigned on every success path"
            )

        self._dispatcher.dispatch(events)
        return ApplicationResult.ok(performance_id, warnings=warnings)
