"""`RecordProgressHandler`: records a brand-new Progress check-in for an
existing User, and surfaces `ProgressEvaluationRuleEngine` advice as
warnings.

Orchestrates two repositories (`UserRepository`, `ProgressRepository`)
within one `UnitOfWork` — the existence check against `UserRepository`
is a referential-integrity check ("does this user exist"), not a
business rule, the identical reasoning `RecordNutritionHandler`
(`app.application.nutrition.handlers.record_nutrition_handler`)
documents for its own `UserRepository` check. Every decision about what
makes a `Progress` record valid still lives on `Progress`/its value
objects themselves.

`ProgressEvaluationRuleEngine` is evaluated once, after
`UnitOfWork.commit()`, from the user's *full* check-in history —
`ConsistencyRule`/`PlateauRule`/`MeasurementTrendRule` are inherently
about trends across many records, not just the one just recorded, the
same "historical summaries already supplied by the application layer"
role `CompleteWorkoutSessionHandler`
(`app.application.workout.handlers.complete_workout_session_handler`)
documents for its own trend-based engines. `goal` is always `None`: no
`GoalRepository` exists in this phase's required repository list (Goal
Application Use Cases are a later phase), so `BodyWeightRule`/
`BodyFatRule` — the two rules in this engine that read `context.goal` —
always take their documented "no active goal supplied" pass path; see
`docs/adr/0026-progress-application-use-cases.md`. The engine is
evaluation-only and can never fail this workflow; its `recommendations`
are surfaced as `ApplicationResult.warnings`, never a reason to fail the
command.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.progress.commands.record_progress import RecordProgressCommand
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.progress.identifiers import ProgressId
from app.domain.progress.progress import Progress
from app.domain.progress.repository import ProgressRepository
from app.domain.progress.rules.context import ProgressEvaluationRuleContext
from app.domain.progress.rules.progress_evaluation_rule_engine import ProgressEvaluationRuleEngine
from app.domain.rules.result import RuleResult
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.repository import UserRepository

_rule_engine = ProgressEvaluationRuleEngine()


def _advisory_warnings(result: RuleResult) -> tuple[str, ...]:
    """Formats a `RuleResult`'s `recommendations` as human-readable
    strings, e.g. `"[advisory] log progress more regularly..."`.
    Duplicated per handler file in this package rather than factored
    into a shared module — the same "two call sites sharing one
    three-line function is not yet the second real need" reasoning
    `docs/adr/0024-workout-application-use-cases.md` gives for its own
    identical helper.
    """
    return tuple(
        f"[{recommendation.severity.value}] {recommendation.message}"
        for recommendation in result.recommendations
    )


class RecordProgressHandler(CommandHandler[RecordProgressCommand, ProgressId]):
    """Records a new Progress check-in and returns its freshly generated
    `ProgressId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: RecordProgressCommand) -> ApplicationResult[ProgressId]:
        progress_id = ProgressId.generate()
        events: Sequence[DomainEvent] = ()
        warnings: tuple[str, ...] = ()

        try:
            with self._uow as uow:
                # UserRepository/ProgressRepository have no concrete
                # implementation in this phase (by design); mypy's
                # type-abstract check assumes a type[T] argument might be
                # instantiated, but get_repository only ever uses it as a
                # lookup key — a documented, narrow false positive, the
                # same one every prior handler in this codebase already
                # carries.
                user_repository = uow.get_repository(UserRepository)  # type: ignore[type-abstract]
                user = user_repository.get(request.user_id)
                if user is None:
                    uow.rollback()
                    return ApplicationResult.fail([f"user {request.user_id} not found"])

                progress = Progress.record(
                    progress_id=progress_id,
                    user_id=request.user_id,
                    progress_date=request.progress_date,
                    unit=request.unit,
                    source=request.source,
                    body_weight=request.body_weight,
                    body_fat_percentage=request.body_fat_percentage,
                    lean_body_mass=request.lean_body_mass,
                    muscle_mass=request.muscle_mass,
                    waist=request.waist,
                    chest=request.chest,
                    hip=request.hip,
                    arm=request.arm,
                    thigh=request.thigh,
                    calf=request.calf,
                    neck=request.neck,
                    notes=request.notes,
                    clock=self._clock,
                )
                progress_repository = uow.get_repository(
                    ProgressRepository  # type: ignore[type-abstract]
                )
                progress_repository.add(progress)
                uow.commit()
                events = progress.pull_domain_events()

                history = progress_repository.list_by_user(request.user_id)
                rule_context = ProgressEvaluationRuleContext.from_aggregates(
                    progress_records=history, goal=None, clock=self._clock
                )
                rule_result = _rule_engine.evaluate(rule_context)
                warnings = _advisory_warnings(rule_result)
        except DomainInvariantViolationError:
            # Progress.record() only ever raises via `ensure(recorded_at.
            # tzinfo is not None, ...)` (progress.py), and every Clock
            # implementation in this codebase returns a timezone-aware
            # `datetime` — this branch is therefore currently unreachable,
            # kept for defensive future-proofing consistency with every
            # other mutating handler in this codebase, the same reasoning
            # `docs/adr/0024-workout-application-use-cases.md` gives for
            # its own identical, currently-unreachable guards.
            raise  # pragma: no cover
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(events)
        return ApplicationResult.ok(progress_id, warnings=warnings)
