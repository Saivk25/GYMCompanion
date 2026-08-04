"""`RecordNutritionHandler`: records a brand-new Nutrition entry for an
existing User, and surfaces `NutritionRuleEngine` advice as warnings.

Orchestrates two repositories (`UserRepository`, `NutritionRepository`)
within one `UnitOfWork` — the existence check against `UserRepository`
is a referential-integrity check ("does this user exist"), not a
business rule, the identical reasoning `CreateWorkoutHandler`
(`app.application.workout.handlers.create_workout_handler`) documents
for its own `UserRepository` check. Every decision about what makes a
`Nutrition` entry valid still lives on `Nutrition`/its value objects
themselves.

`NutritionRuleEngine` is evaluated once, after `UnitOfWork.commit()`,
from a `NutritionRuleContext` built directly off the just-recorded
aggregate (`NutritionRuleContext.from_nutrition(nutrition)`) — no
history, no repository access needed, since every rule in this engine
evaluates one entry's own fields in isolation (`docs/adr/0025-
nutrition-application-use-cases.md`). The engine is evaluation-only and
can never fail this workflow; its `recommendations` are surfaced as
`ApplicationResult.warnings`, never a reason to fail the command.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.nutrition.commands.record_nutrition import RecordNutritionCommand
from app.application.shared.advisory_warnings import advisory_warnings
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.nutrition import Nutrition
from app.domain.nutrition.repository import NutritionRepository
from app.domain.nutrition.rules.context import NutritionRuleContext
from app.domain.nutrition.rules.nutrition_rule_engine import NutritionRuleEngine
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.repository import UserRepository

_rule_engine = NutritionRuleEngine()


class RecordNutritionHandler(CommandHandler[RecordNutritionCommand, NutritionId]):
    """Records a new Nutrition entry and returns its freshly generated
    `NutritionId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: RecordNutritionCommand) -> ApplicationResult[NutritionId]:
        nutrition_id = NutritionId.generate()
        events: Sequence[DomainEvent] = ()
        warnings: tuple[str, ...] = ()

        try:
            with self._uow as uow:
                # UserRepository/NutritionRepository have no concrete
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

                nutrition = Nutrition.record(
                    nutrition_id=nutrition_id,
                    user_id=request.user_id,
                    nutrition_date=request.nutrition_date,
                    meal_type=request.meal_type,
                    source=request.source,
                    calories=request.calories,
                    protein=request.protein,
                    carbohydrates=request.carbohydrates,
                    fat=request.fat,
                    fiber=request.fiber,
                    sugar=request.sugar,
                    water_intake=request.water_intake,
                    notes=request.notes,
                    clock=self._clock,
                )
                nutrition_repository = uow.get_repository(
                    NutritionRepository  # type: ignore[type-abstract]
                )
                nutrition_repository.add(nutrition)
                uow.commit()
                events = nutrition.pull_domain_events()

                rule_result = _rule_engine.evaluate(NutritionRuleContext.from_nutrition(nutrition))
                warnings = advisory_warnings(rule_result)
        except DomainInvariantViolationError:
            # Nutrition.record() only ever raises via `ensure(recorded_at.
            # tzinfo is not None, ...)` (nutrition.py), and every Clock
            # implementation in this codebase returns a timezone-aware
            # `datetime` — this branch is therefore currently unreachable,
            # kept for defensive future-proofing consistency with every
            # other mutating handler in this codebase, the same reasoning
            # `docs/adr/0024-workout-application-use-cases.md` gives for its
            # own identical, currently-unreachable guards.
            raise  # pragma: no cover
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(events)
        return ApplicationResult.ok(nutrition_id, warnings=warnings)
