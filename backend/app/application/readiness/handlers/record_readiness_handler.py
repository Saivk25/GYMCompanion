"""`RecordReadinessHandler`: records a brand-new Readiness check-in for
an existing User, and surfaces `ReadinessRuleEngine` advice as warnings.

Orchestrates two repositories (`UserRepository`, `ReadinessRepository`)
within one `UnitOfWork` — the existence check against `UserRepository`
is a referential-integrity check ("does this user exist"), not a
business rule, the identical reasoning `RecordProgressHandler`
(`app.application.progress.handlers.record_progress_handler`) documents
for its own `UserRepository` check. Every decision about what makes a
`Readiness` check-in valid still lives on `Readiness`/its value objects
themselves.

`ReadinessRuleEngine` is evaluated once, after `UnitOfWork.commit()`,
from a `ReadinessRuleContext` built directly off the just-recorded
aggregate (`ReadinessRuleContext.from_readiness(readiness)`) — no
history, no repository access needed, since every rule in this engine
evaluates one check-in's own fields in isolation, the same shape
`RecordNutritionHandler`'s own module docstring documents for
`NutritionRuleContext.from_nutrition()` (`docs/adr/0027-readiness-
application-use-cases.md`). The engine is evaluation-only and can never
fail this workflow; its `recommendations` are surfaced as
`ApplicationResult.warnings`, never a reason to fail the command.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.readiness.commands.record_readiness import RecordReadinessCommand
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.readiness import Readiness
from app.domain.readiness.repository import ReadinessRepository
from app.domain.readiness.rules.context import ReadinessRuleContext
from app.domain.readiness.rules.readiness_rule_engine import ReadinessRuleEngine
from app.domain.rules.result import RuleResult
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.repository import UserRepository

_rule_engine = ReadinessRuleEngine()


def _advisory_warnings(result: RuleResult) -> tuple[str, ...]:
    """Formats a `RuleResult`'s `recommendations` as human-readable
    strings, e.g. `"[advisory] consider prioritizing sleep tonight"`.
    Duplicated per handler file in this package rather than factored
    into a shared module — the same "two call sites sharing one
    three-line function is not yet the second real need" reasoning
    `docs/adr/0024-workout-application-use-cases.md` gives for its own
    identical helper. See `docs/TECH_DEBT.md`'s TD-0001: this
    duplication is tracked, not accidental — 9 copies now exist across
    Workout/Nutrition/Progress/Readiness, which is exactly the "9th call
    site" trigger condition TD-0001 names for extraction.
    """
    return tuple(
        f"[{recommendation.severity.value}] {recommendation.message}"
        for recommendation in result.recommendations
    )


class RecordReadinessHandler(CommandHandler[RecordReadinessCommand, ReadinessId]):
    """Records a new Readiness check-in and returns its freshly
    generated `ReadinessId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: RecordReadinessCommand) -> ApplicationResult[ReadinessId]:
        readiness_id = ReadinessId.generate()
        events: Sequence[DomainEvent] = ()
        warnings: tuple[str, ...] = ()

        try:
            with self._uow as uow:
                # UserRepository/ReadinessRepository have no concrete
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

                readiness: Readiness = Readiness.record(
                    readiness_id=readiness_id,
                    user_id=request.user_id,
                    readiness_date=request.readiness_date,
                    source=request.source,
                    sleep_duration=request.sleep_duration,
                    sleep_quality=request.sleep_quality,
                    energy_level=request.energy_level,
                    stress_level=request.stress_level,
                    soreness_level=request.soreness_level,
                    resting_heart_rate=request.resting_heart_rate,
                    heart_rate_variability=request.heart_rate_variability,
                    notes=request.notes,
                    clock=self._clock,
                )
                readiness_repository = uow.get_repository(
                    ReadinessRepository  # type: ignore[type-abstract]
                )
                readiness_repository.add(readiness)
                uow.commit()
                events = readiness.pull_domain_events()

                rule_result = _rule_engine.evaluate(ReadinessRuleContext.from_readiness(readiness))
                warnings = _advisory_warnings(rule_result)
        except DomainInvariantViolationError:
            # Readiness.record() only ever raises via `ensure(recorded_at.
            # tzinfo is not None, ...)` (readiness.py), and every Clock
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
        return ApplicationResult.ok(readiness_id, warnings=warnings)
