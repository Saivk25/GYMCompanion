"""`UpdateGoalHandler`: replaces whichever fields are given on an
existing, Active Goal, and surfaces `GoalAlignmentRuleEngine` advice as
warnings.

Single-aggregate, full-replace, same shape as
`app.application.workout.handlers.update_workout_handler.
UpdateWorkoutHandler`: one command wraps `Goal.update(...)`'s whole
field set, matching that aggregate method being a single call rather
than several narrower ones (see `UpdateGoalCommand`'s own module
docstring). `Goal.update(...)`'s own "`None` means leave unchanged, not
clear it" semantics are forwarded untouched.

Unlike `CreateWorkoutHandler`/`CancelWorkoutHandler`,
`DomainInvariantViolationError` here is genuinely reachable, not a
defensive unreachable guard: `Goal.update()` calls `_ensure_mutable()`,
which raises when the goal is not `GoalStatus.ACTIVE` — e.g. updating an
already-Completed or -Cancelled goal. This handler therefore re-raises
it uncaught rather than converting it to a failed `ApplicationResult`,
the identical choice `UpdateWorkoutHandler`
(`app.application.workout.handlers.update_workout_handler`) already
makes for its own reachable `Workout._ensure_mutable()` violation — see
`docs/adr/0028-goal-application-use-cases.md`.

Re-evaluates `GoalAlignmentRuleEngine` from the whole aggregate's
current state after a successful update — `update()` cannot change
`status`, so a goal that reached this point (no exception raised) is
still Active, meaning the re-evaluation is always meaningful, unlike
`CompleteGoalHandler`/`CancelGoalHandler` (see those handlers' own
docstrings). `progress` is deliberately `None` in the rule context built
here — see `CreateGoalHandler`'s own docstring for why.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.goal.commands.update_goal import UpdateGoalCommand
from app.application.shared.advisory_warnings import advisory_warnings
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.goal.identifiers import GoalId
from app.domain.goal.repository import GoalRepository
from app.domain.goal.rules.context import GoalAlignmentRuleContext
from app.domain.goal.rules.goal_alignment_rule_engine import GoalAlignmentRuleEngine
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent

_rule_engine = GoalAlignmentRuleEngine()


class UpdateGoalHandler(CommandHandler[UpdateGoalCommand, GoalId]):
    """Loads a Goal, replaces whichever fields are given, and returns
    the same `GoalId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: UpdateGoalCommand) -> ApplicationResult[GoalId]:
        events: Sequence[DomainEvent] = ()
        warnings: tuple[str, ...] = ()

        try:
            with self._uow as uow:
                # GoalRepository has no concrete implementation in this
                # phase (by design); mypy's type-abstract check assumes a
                # type[T] argument might be instantiated, but get_repository
                # only ever uses it as a lookup key, so this is a documented,
                # narrow false positive.
                repository = uow.get_repository(GoalRepository)  # type: ignore[type-abstract]
                goal = repository.get(request.goal_id)
                if goal is None:
                    uow.rollback()
                    return ApplicationResult.fail([f"goal {request.goal_id} not found"])

                goal.update(
                    clock=self._clock,
                    name=request.name,
                    description=request.description,
                    target_date=request.target_date,
                    target_weight=request.target_weight,
                    target_body_fat=request.target_body_fat,
                    target_strength=request.target_strength,
                    priority=request.priority,
                    notes=request.notes,
                )
                uow.commit()
                events = goal.pull_domain_events()

                rule_context = GoalAlignmentRuleContext.from_aggregates(
                    goal=goal, progress=None, clock=self._clock
                )
                rule_result = _rule_engine.evaluate(rule_context)
                warnings = advisory_warnings(rule_result)
        except DomainInvariantViolationError:
            raise
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(events)
        return ApplicationResult.ok(request.goal_id, warnings=warnings)
