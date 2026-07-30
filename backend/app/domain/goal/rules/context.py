"""`GoalAlignmentRuleContext`: the `RuleContext` (`app.domain.rules`)
subtype every goal alignment rule in this package evaluates against.

Unlike `app.domain.readiness.rules.context.ReadinessRuleContext` and
`app.domain.nutrition.rules.context.NutritionRuleContext` — both of which
flatten their source aggregate's fields directly into the context's own
fields — this context *references whole snapshots*: a `GoalContext` and,
optionally, a `ProgressContext`. Goal Alignment inherently needs almost
everything each of those two existing types already carries (target date,
target weight, target body fat, target strength, priority, and status
from `Goal`; current body weight and body fat from `Progress`), so
re-flattening every one of those fields into new, differently-named
fields here would duplicate structure `GoalContext`/`ProgressContext`
already provide, for no benefit — see
`docs/adr/0016-goal-alignment-combines-whole-snapshots.md` for the full
reasoning.

No circular import risk in reaching into two sibling aggregate packages
this way: `app.domain.goal.rules` depends on `app.domain.goal` and
`app.domain.progress`, and neither of those depends back on
`app.domain.goal.rules` — a one-directional dependency, the same shape
`app/domain/test_import_boundaries.py` already enforces for the whole
domain layer, just one level more specific here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.goal.context import GoalContext
from app.domain.goal.goal import Goal
from app.domain.progress.context import ProgressContext
from app.domain.progress.progress import Progress
from app.domain.rules.context import RuleContext
from app.domain.shared_kernel.clock import Clock


@dataclass(frozen=True, kw_only=True)
class GoalAlignmentRuleContext(RuleContext):
    """One evaluation's worth of goal alignment data: exactly one goal's
    snapshot, an optional most-recent progress snapshot to compare it
    against, and the date to evaluate "approaching" / "overdue" relative
    to.

    `reference_date` is deliberately a field here, not something a rule
    reads from the system clock internally — `Rule.evaluate()`'s own
    contract (`app.domain.rules.rule`) requires "no wall-clock reads,"
    exactly because a rule that quietly called `date.today()` would stop
    being a pure function of its context: the same
    `GoalAlignmentRuleContext` evaluated on two different days would
    produce two different `TargetDateRule` results, which is not what
    "deterministic" means here. Supplying it explicitly (typically from a
    `Clock`, via `from_aggregates` below) keeps every rule's determinism
    guarantee intact.
    """

    goal: GoalContext
    progress: ProgressContext | None = None
    reference_date: date

    @classmethod
    def from_snapshots(
        cls,
        *,
        goal: GoalContext,
        progress: ProgressContext | None = None,
        reference_date: date,
    ) -> GoalAlignmentRuleContext:
        """Builds a context directly from already-built snapshots — the
        primary constructor path once a caller already has a `GoalContext`
        and, optionally, a `ProgressContext` in hand (e.g. from its own
        repository lookups; this package performs none itself)."""
        return cls(goal=goal, progress=progress, reference_date=reference_date)

    @classmethod
    def from_aggregates(
        cls, *, goal: Goal, progress: Progress | None, clock: Clock
    ) -> GoalAlignmentRuleContext:
        """Convenience path from live aggregates: snapshots them via their
        own existing `GoalContext.from_goal()` / `ProgressContext.
        from_progress()` factories and stamps `reference_date` from
        `clock.now().date()` — the same "caller supplies a `Clock`, never
        reads the system clock directly" discipline every aggregate
        factory in this codebase already follows. Takes the aggregates
        themselves, not a repository — this package declares no
        repository or service dependency of its own; loading `Goal`/
        `Progress` first is a caller concern.
        """
        return cls(
            goal=GoalContext.from_goal(goal),
            progress=ProgressContext.from_progress(progress) if progress is not None else None,
            reference_date=clock.now().date(),
        )
