"""`UpdateMeasurementsHandler`: replaces whichever tape measurements are
given on an existing Progress record, and surfaces
`ProgressEvaluationRuleEngine` advice as warnings.

Mirrors `UpdateBodyCompositionHandler`'s shape exactly but calls
`Progress.update_measurements()` instead — kept as its own handler
because `update_measurements()` is its own aggregate method with its own
event (`MeasurementsUpdated`), matching `UpdateMeasurementsCommand`'s own
module docstring.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.progress.commands.update_measurements import UpdateMeasurementsCommand
from app.application.shared.advisory_warnings import advisory_warnings
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.ownership import ensure_owner
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.progress.identifiers import ProgressId
from app.domain.progress.repository import ProgressRepository
from app.domain.progress.rules.context import ProgressEvaluationRuleContext
from app.domain.progress.rules.progress_evaluation_rule_engine import ProgressEvaluationRuleEngine
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent

_rule_engine = ProgressEvaluationRuleEngine()


class UpdateMeasurementsHandler(CommandHandler[UpdateMeasurementsCommand, ProgressId]):
    """Loads a Progress record, replaces whichever tape measurements are
    given, and returns the same `ProgressId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: UpdateMeasurementsCommand) -> ApplicationResult[ProgressId]:
        events: Sequence[DomainEvent] = ()
        warnings: tuple[str, ...] = ()

        try:
            with self._uow as uow:
                # ProgressRepository has no concrete implementation in this
                # phase (by design); mypy's type-abstract check assumes a
                # type[T] argument might be instantiated, but get_repository
                # only ever uses it as a lookup key, so this is a documented,
                # narrow false positive.
                repository = uow.get_repository(
                    ProgressRepository  # type: ignore[type-abstract]
                )
                progress = repository.get(request.progress_id)
                if progress is None:
                    uow.rollback()
                    return ApplicationResult.fail(
                        [f"progress record {request.progress_id} not found"]
                    )

                denial = ensure_owner(owner_id=progress.user_id, requester_id=request.requester_id)
                if denial is not None:
                    uow.rollback()
                    return ApplicationResult.forbid([denial])

                progress.update_measurements(
                    waist=request.waist,
                    chest=request.chest,
                    hip=request.hip,
                    arm=request.arm,
                    thigh=request.thigh,
                    calf=request.calf,
                    neck=request.neck,
                    clock=self._clock,
                )
                uow.commit()
                events = progress.pull_domain_events()

                history = repository.list_by_user(progress.user_id)
                rule_context = ProgressEvaluationRuleContext.from_aggregates(
                    progress_records=history, goal=None, clock=self._clock
                )
                rule_result = _rule_engine.evaluate(rule_context)
                warnings = advisory_warnings(rule_result)
        except DomainInvariantViolationError:
            # Progress.update_measurements() has no status/lifecycle guard
            # to violate (progress.py's own module docstring: "no status
            # enum and no lifecycle") and raises no
            # `DomainInvariantViolationError` of its own — this branch is
            # therefore currently unreachable, kept for defensive
            # future-proofing consistency with every other mutating
            # handler in this codebase, the same reasoning
            # `docs/adr/0024-workout-application-use-cases.md` gives for
            # its own identical, currently-unreachable guards.
            raise  # pragma: no cover
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(events)
        return ApplicationResult.ok(request.progress_id, warnings=warnings)
