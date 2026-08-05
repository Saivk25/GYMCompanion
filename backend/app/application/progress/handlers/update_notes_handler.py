"""`UpdateNotesHandler`: replaces an existing Progress record's notes
wholesale.

No `ProgressEvaluationRuleEngine` evaluation here, unlike
`RecordProgressHandler`/`UpdateBodyCompositionHandler`/
`UpdateMeasurementsHandler` — notes are not a field any of
`ProgressEvaluationRuleContext`'s five rules read (`BodyWeightRule`,
`BodyFatRule`, `MeasurementTrendRule`, `ConsistencyRule`, `PlateauRule`
all evaluate body-composition/measurement/date fields only), so
re-evaluating the engine after a notes-only change would produce a
result byte-for-byte identical to whatever the last rule-relevant
mutation already produced — the same "rule-relevant fields only" scope
`docs/adr/0025-nutrition-application-use-cases.md` draws for which
Nutrition handlers wire in `NutritionRuleEngine`. See
`docs/adr/0026-progress-application-use-cases.md`.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.progress.commands.update_notes import UpdateNotesCommand
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.ownership import ensure_owner
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.progress.identifiers import ProgressId
from app.domain.progress.repository import ProgressRepository
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent


class UpdateNotesHandler(CommandHandler[UpdateNotesCommand, ProgressId]):
    """Loads a Progress record, replaces its notes, and returns the same
    `ProgressId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: UpdateNotesCommand) -> ApplicationResult[ProgressId]:
        events: Sequence[DomainEvent] = ()

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

                progress.update_notes(request.notes, clock=self._clock)
                uow.commit()
                events = progress.pull_domain_events()
        except DomainInvariantViolationError:
            # Progress.update_notes() has no status/lifecycle guard to
            # violate (progress.py's own module docstring: "no status enum
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
        return ApplicationResult.ok(request.progress_id)
