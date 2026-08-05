"""`UpdateNutritionNotesHandler`: replaces an existing Nutrition entry's
notes wholesale.

No `NutritionRuleEngine` evaluation here, unlike `RecordNutritionHandler`/
`UpdateNutritionHandler`/`UpdateWaterHandler` — `notes` is explicitly
excluded from `NutritionRuleContext` (see that module's docstring: "no
`notes`, and — notably — no ..."), so re-evaluating the engine after a
notes-only change would produce a result byte-for-byte identical to
whatever the last rule-relevant mutation already produced — the same
"rule-relevant fields only" reasoning `UpdateNotesHandler`
(`app.application.progress.handlers.update_notes_handler`) documents for
`Progress.update_notes()`. See `docs/adr/0025-nutrition-application-use-
cases.md`.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.nutrition.commands.update_notes import UpdateNutritionNotesCommand
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.ownership import ensure_owner
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.repository import NutritionRepository
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent


class UpdateNutritionNotesHandler(CommandHandler[UpdateNutritionNotesCommand, NutritionId]):
    """Loads a Nutrition entry, replaces its notes, and returns the same
    `NutritionId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: UpdateNutritionNotesCommand) -> ApplicationResult[NutritionId]:
        events: Sequence[DomainEvent] = ()

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

                nutrition.update_notes(request.notes, clock=self._clock)
                uow.commit()
                events = nutrition.pull_domain_events()
        except DomainInvariantViolationError:
            # Nutrition.update_notes() has no status/lifecycle guard to
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
        return ApplicationResult.ok(request.nutrition_id)
