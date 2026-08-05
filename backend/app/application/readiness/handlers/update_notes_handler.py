"""`UpdateNotesHandler`: replaces an existing Readiness check-in's notes
wholesale.

No `ReadinessRuleEngine` evaluation here, unlike `RecordReadinessHandler`/
`UpdateSleepHandler`/`UpdateRecoveryMetricsHandler` — `notes` is
explicitly excluded from `ReadinessRuleContext` (see that module's own
docstring: "No `readiness_id`, no `user_id`, no `notes`"), so
re-evaluating the engine after a notes-only change would produce a
result byte-for-byte identical to whatever the last rule-relevant
mutation already produced — the same "rule-relevant fields only"
reasoning `UpdateNotesHandler`
(`app.application.progress.handlers.update_notes_handler`) documents for
`Progress.update_notes()`. See `docs/adr/0027-readiness-application-use-
cases.md`.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.readiness.commands.update_notes import UpdateNotesCommand
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.ownership import ensure_owner
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.repository import ReadinessRepository
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent


class UpdateNotesHandler(CommandHandler[UpdateNotesCommand, ReadinessId]):
    """Loads a Readiness check-in, replaces its notes, and returns the
    same `ReadinessId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: UpdateNotesCommand) -> ApplicationResult[ReadinessId]:
        events: Sequence[DomainEvent] = ()

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

                denial = ensure_owner(owner_id=readiness.user_id, requester_id=request.requester_id)
                if denial is not None:
                    uow.rollback()
                    return ApplicationResult.forbid([denial])

                readiness.update_notes(request.notes, clock=self._clock)
                uow.commit()
                events = readiness.pull_domain_events()
        except DomainInvariantViolationError:
            # Readiness.update_notes() has no status/lifecycle guard to
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
        return ApplicationResult.ok(request.readiness_id)
