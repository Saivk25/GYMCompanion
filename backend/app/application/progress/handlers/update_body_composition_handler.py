"""`UpdateBodyCompositionHandler`: replaces whichever body-composition
fields are given on an existing Progress record, and surfaces
`ProgressEvaluationRuleEngine` advice as warnings.

Single-aggregate load/mutate/commit/dispatch shape, then evaluates the
rule engine from the user's full check-in history (via
`ProgressRepository.list_by_user()`, using the already-loaded record's
own `user_id` — no extra command field needed) — see
`RecordProgressHandler`'s module docstring for why the engine needs the
whole history, not just this one record, and why `goal` is always
`None` in this phase.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.progress.commands.update_body_composition import (
    UpdateBodyCompositionCommand,
)
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


class UpdateBodyCompositionHandler(CommandHandler[UpdateBodyCompositionCommand, ProgressId]):
    """Loads a Progress record, replaces whichever body-composition
    fields are given, and returns the same `ProgressId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: UpdateBodyCompositionCommand) -> ApplicationResult[ProgressId]:
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

                progress.update_body_composition(
                    body_weight=request.body_weight,
                    body_fat_percentage=request.body_fat_percentage,
                    lean_body_mass=request.lean_body_mass,
                    muscle_mass=request.muscle_mass,
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
            # Progress.update_body_composition() has no status/lifecycle
            # guard to violate (progress.py's own module docstring: "no
            # status enum and no lifecycle") and raises no
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
