"""`UpdateSleepHandler`: replaces whichever sleep fields are given on an
existing Readiness check-in, and surfaces `ReadinessRuleEngine` advice as
warnings.

Single-aggregate, same load/mutate/commit/dispatch shape as
`app.application.nutrition.handlers.update_nutrition_handler.
UpdateNutritionHandler`. `Readiness.update_sleep(...)`'s own "`None`
means leave unchanged" semantics are forwarded untouched — see
`UpdateSleepCommand`'s module docstring for why this handler performs
no `None`-substitution logic of its own. Re-evaluates
`ReadinessRuleEngine` from the whole aggregate's current state via
`ReadinessRuleContext.from_readiness(readiness)`, not just the fields
this call changed — `SleepRule` reads `sleep_duration`, which this
handler can change, so re-evaluation is rule-relevant here, unlike
`UpdateNotesHandler`.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.readiness.commands.update_sleep import UpdateSleepCommand
from app.application.shared.advisory_warnings import advisory_warnings
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.repository import ReadinessRepository
from app.domain.readiness.rules.context import ReadinessRuleContext
from app.domain.readiness.rules.readiness_rule_engine import ReadinessRuleEngine
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent

_rule_engine = ReadinessRuleEngine()


class UpdateSleepHandler(CommandHandler[UpdateSleepCommand, ReadinessId]):
    """Loads a Readiness check-in, replaces whichever sleep fields are
    given, and returns the same `ReadinessId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: UpdateSleepCommand) -> ApplicationResult[ReadinessId]:
        events: Sequence[DomainEvent] = ()
        warnings: tuple[str, ...] = ()

        try:
            with self._uow as uow:
                # ReadinessRepository has no concrete implementation in this
                # phase (by design); mypy's type-abstract check assumes a
                # type[T] argument might be instantiated, but get_repository
                # only ever uses it as a lookup key, so this is a documented,
                # narrow false positive.
                repository = uow.get_repository(
                    ReadinessRepository  # type: ignore[type-abstract]
                )
                readiness = repository.get(request.readiness_id)
                if readiness is None:
                    uow.rollback()
                    return ApplicationResult.fail(
                        [f"readiness check-in {request.readiness_id} not found"]
                    )

                readiness.update_sleep(
                    sleep_duration=request.sleep_duration,
                    sleep_quality=request.sleep_quality,
                    clock=self._clock,
                )
                uow.commit()
                events = readiness.pull_domain_events()

                rule_result = _rule_engine.evaluate(ReadinessRuleContext.from_readiness(readiness))
                warnings = advisory_warnings(rule_result)
        except DomainInvariantViolationError:
            # Readiness.update_sleep() has no status/lifecycle guard to
            # violate (readiness.py's own module docstring: "no status
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
        return ApplicationResult.ok(request.readiness_id, warnings=warnings)
