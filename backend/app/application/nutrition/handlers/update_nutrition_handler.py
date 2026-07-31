"""`UpdateNutritionHandler`: replaces whichever macro/calorie fields are
given on an existing Nutrition entry, and surfaces `NutritionRuleEngine`
advice as warnings.

Single-aggregate, same load/mutate/commit/dispatch shape as
`app.application.workout.handlers.update_workout_handler.
UpdateWorkoutHandler`. `Nutrition.update_nutrition(...)`'s own "`None`
means leave unchanged" semantics are forwarded untouched — see
`UpdateNutritionCommand`'s module docstring for why this handler
performs no `None`-substitution logic of its own.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.nutrition.commands.update_nutrition import UpdateNutritionCommand
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.repository import NutritionRepository
from app.domain.nutrition.rules.context import NutritionRuleContext
from app.domain.nutrition.rules.nutrition_rule_engine import NutritionRuleEngine
from app.domain.rules.result import RuleResult
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent

_rule_engine = NutritionRuleEngine()


def _advisory_warnings(result: RuleResult) -> tuple[str, ...]:
    """Formats a `RuleResult`'s `recommendations` as human-readable
    strings. See `RecordNutritionHandler`'s identical helper."""
    return tuple(
        f"[{recommendation.severity.value}] {recommendation.message}"
        for recommendation in result.recommendations
    )


class UpdateNutritionHandler(CommandHandler[UpdateNutritionCommand, NutritionId]):
    """Loads a Nutrition entry, replaces whichever macro/calorie fields
    are given, and returns the same `NutritionId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: UpdateNutritionCommand) -> ApplicationResult[NutritionId]:
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

                nutrition.update_nutrition(
                    calories=request.calories,
                    protein=request.protein,
                    carbohydrates=request.carbohydrates,
                    fat=request.fat,
                    fiber=request.fiber,
                    sugar=request.sugar,
                    clock=self._clock,
                )
                uow.commit()
                events = nutrition.pull_domain_events()

                rule_result = _rule_engine.evaluate(NutritionRuleContext.from_nutrition(nutrition))
                warnings = _advisory_warnings(rule_result)
        except DomainInvariantViolationError:
            # Nutrition.update_nutrition() has no status/lifecycle guard to
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
