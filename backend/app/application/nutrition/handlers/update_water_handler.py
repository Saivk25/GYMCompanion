"""`UpdateWaterHandler`: replaces an existing Nutrition entry's water
intake, and surfaces `NutritionRuleEngine` advice as warnings.

Single-aggregate, mirrors `UpdateNutritionHandler`'s shape exactly but
calls `Nutrition.update_water()` instead — kept as its own handler
because `update_water()` is its own aggregate method with its own
event (`WaterUpdated`), matching `UpdateWaterCommand`'s own module
docstring.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.nutrition.commands.update_water import UpdateWaterCommand
from app.application.shared.advisory_warnings import advisory_warnings
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.ownership import ensure_owner
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.repository import NutritionRepository
from app.domain.nutrition.rules.context import NutritionRuleContext
from app.domain.nutrition.rules.nutrition_rule_engine import NutritionRuleEngine
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent

_rule_engine = NutritionRuleEngine()


class UpdateWaterHandler(CommandHandler[UpdateWaterCommand, NutritionId]):
    """Loads a Nutrition entry, replaces its water intake, and returns
    the same `NutritionId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: UpdateWaterCommand) -> ApplicationResult[NutritionId]:
        events: Sequence[DomainEvent] = ()
        warnings: tuple[str, ...] = ()

        try:
            with self._uow as uow:
                # NutritionRepository has no concrete implementation in this
                # phase (by design); mypy's type-abstract check assumes a
                # type[T] argument might be instantiated, but get_repository
                # only ever uses it as a lookup key, so this is a documented,
                # narrow false positive.
                repository = uow.get_repository(
                    NutritionRepository  # type: ignore[type-abstract]
                )
                nutrition = repository.get(request.nutrition_id)
                if nutrition is None:
                    uow.rollback()
                    return ApplicationResult.fail(
                        [f"nutrition entry {request.nutrition_id} not found"]
                    )

                denial = ensure_owner(owner_id=nutrition.user_id, requester_id=request.requester_id)
                if denial is not None:
                    uow.rollback()
                    return ApplicationResult.forbid([denial])

                nutrition.update_water(request.water_intake, clock=self._clock)
                uow.commit()
                events = nutrition.pull_domain_events()

                rule_result = _rule_engine.evaluate(NutritionRuleContext.from_nutrition(nutrition))
                warnings = advisory_warnings(rule_result)
        except DomainInvariantViolationError:
            # Nutrition.update_water() has no status/lifecycle guard to
            # violate (nutrition.py's own module docstring: "no status enum
            # and no lifecycle") and raises no `DomainInvariantViolationError`
            # of its own — this branch is therefore currently unreachable,
            # kept for defensive future-proofing consistency with every
            # other mutating handler in this codebase, the same reasoning
            # `docs/adr/0024-workout-application-use-cases.md` gives for its
            # own identical, currently-unreachable guards.
            raise  # pragma: no cover
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(events)
        return ApplicationResult.ok(request.nutrition_id, warnings=warnings)
