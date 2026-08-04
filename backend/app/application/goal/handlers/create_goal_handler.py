"""`CreateGoalHandler`: creates a brand-new, Active Goal for an existing
User, and surfaces `GoalAlignmentRuleEngine` advice as warnings.

Orchestrates two repositories (`UserRepository`, `GoalRepository`)
within one `UnitOfWork` — the existence check against `UserRepository`
is a referential-integrity check ("does this user exist"), not a
business rule, the identical reasoning `RecordReadinessHandler`
(`app.application.readiness.handlers.record_readiness_handler`)
documents for its own `UserRepository` check. Every decision about what
makes a `Goal` valid still lives on `Goal`/its value objects themselves.

`GoalAlignmentRuleEngine` is evaluated once, after `UnitOfWork.commit()`,
from a `GoalAlignmentRuleContext` built via
`GoalAlignmentRuleContext.from_aggregates(goal=goal, progress=None,
clock=self._clock)` — `progress` is deliberately `None`, not a live
`ProgressRepository` lookup, mirroring `ProgressEvaluationRuleContext`'s
own `goal=None` choice in every Progress handler
(`app.application.progress.handlers`, see `docs/adr/0026-progress-
application-use-cases.md`'s decision 6). That ADR names a future Goal
Application Use Cases phase as the point where `GoalRepository` access
would exist to populate its own `goal` field — it does not, by itself,
justify this phase reaching into `ProgressRepository` to populate
`progress` here: doing so would leave the two directions permanently
asymmetric (Goal seeing Progress, Progress still not seeing Goal, since
touching the already-accepted Progress handlers is out of this phase's
scope), a worse inconsistency than both staying deliberately deferred
together. See `docs/adr/0028-goal-application-use-cases.md` for the
full reasoning. The engine is evaluation-only and can never fail this
workflow; its `recommendations` are surfaced as `ApplicationResult.
warnings`, never a reason to fail the command.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.goal.commands.create_goal import CreateGoalCommand
from app.application.shared.advisory_warnings import advisory_warnings
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.goal.goal import Goal
from app.domain.goal.identifiers import GoalId
from app.domain.goal.repository import GoalRepository
from app.domain.goal.rules.context import GoalAlignmentRuleContext
from app.domain.goal.rules.goal_alignment_rule_engine import GoalAlignmentRuleEngine
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.repository import UserRepository

_rule_engine = GoalAlignmentRuleEngine()


class CreateGoalHandler(CommandHandler[CreateGoalCommand, GoalId]):
    """Creates a new Goal and returns its freshly generated `GoalId` on
    success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: CreateGoalCommand) -> ApplicationResult[GoalId]:
        goal_id = GoalId.generate()
        events: Sequence[DomainEvent] = ()
        warnings: tuple[str, ...] = ()

        try:
            with self._uow as uow:
                # UserRepository/GoalRepository have no concrete
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

                goal: Goal = Goal.create(
                    goal_id=goal_id,
                    user_id=request.user_id,
                    goal_type=request.goal_type,
                    name=request.name,
                    target_date=request.target_date,
                    clock=self._clock,
                    description=request.description,
                    target_weight=request.target_weight,
                    target_body_fat=request.target_body_fat,
                    target_strength=request.target_strength,
                    priority=request.priority,
                    notes=request.notes,
                )
                goal_repository = uow.get_repository(GoalRepository)  # type: ignore[type-abstract]
                goal_repository.add(goal)
                uow.commit()
                events = goal.pull_domain_events()

                rule_context = GoalAlignmentRuleContext.from_aggregates(
                    goal=goal, progress=None, clock=self._clock
                )
                rule_result = _rule_engine.evaluate(rule_context)
                warnings = advisory_warnings(rule_result)
        except DomainInvariantViolationError:
            # Goal.create()'s own invariant (a tz-aware created_at) is
            # guaranteed by every Clock implementation in this codebase —
            # this branch is therefore currently unreachable, kept for
            # defensive future-proofing consistency with every other
            # mutating handler in this codebase, the same reasoning
            # `docs/adr/0024-workout-application-use-cases.md` gives for
            # its own identical, currently-unreachable guards.
            raise  # pragma: no cover
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(events)
        return ApplicationResult.ok(goal_id, warnings=warnings)
