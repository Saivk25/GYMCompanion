"""`ProgressEvaluationRuleContext`: the `RuleContext` (`app.domain.rules`)
subtype every progress evaluation rule in this package evaluates against.

Combines two shapes already established by prior phases rather than
inventing a third: an ordered *history* of snapshots, the same shape
`app.domain.workout.rules.context.ProgressiveOverloadRuleContext`
established (ADR 0017) for evaluating trends across many records instead
of one; and a whole, optional `GoalContext` reference, the same shape
`app.domain.goal.rules.context.GoalAlignmentRuleContext` established (ADR
0016) for the same reason — `BodyWeightRule`/`BodyFatRule` below need
most of what `GoalContext` already carries (`target_weight`,
`target_body_fat`, `status`), not a small flattened subset.

`Progress` has no lifecycle/status to filter on unlike `WorkoutSession`
(see `app.domain.progress.progress`'s own module docstring: "no status
enum and no lifecycle... a check-in is a fact, not a multi-step
workflow") — `from_snapshots()` below only sorts by `progress_date`, it
filters nothing.

This package is this codebase's first slice of what
`app.domain.progress.progress`'s own docstring already anticipates:
"Progress Intelligence... a separate, not-yet-built context that reads
this aggregate's events" (Bible Section 4.9/9.3: `Trend`, `PlateauEvent`,
`Forecast`). Only the deterministic-rule slice of that — the Bible's own
Section 10.7 "Progress Rules: governs what trend/plateau/forecast claims
are allowed to be shown" — is built here; the actual statistical
slope/regression computation behind a real `Trend`/`Forecast` entity is
explicitly the Statistical layer's job (Bible Section 8, Table 40: "Rule
Layer... Statistical Layer... AI Advisory Layer"), not this rule engine's,
and remains unbuilt.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from app.domain.goal.context import GoalContext
from app.domain.goal.goal import Goal
from app.domain.progress.context import ProgressContext
from app.domain.progress.progress import Progress
from app.domain.rules.context import RuleContext
from app.domain.shared_kernel.clock import Clock


@dataclass(frozen=True, kw_only=True)
class ProgressEvaluationRuleContext(RuleContext):
    """One evaluation's worth of progress data: an ordered history of
    `ProgressContext` snapshots (oldest first), an optional active goal
    snapshot to evaluate trends against, and the date to evaluate
    logging recency relative to.

    `reference_date` is a required field, not a `date.today()` call
    inside a rule — the same "no wall-clock reads" contract ADR 0016
    documents for `GoalAlignmentRuleContext.reference_date`. Only
    `ConsistencyRule` actually reads it (to check whether the most recent
    entry is recent enough relative to "now") — none of this package's
    other four rules need a notion of "today" at all, the same reasoning
    ADR 0017 documents for why `ProgressiveOverloadRuleContext` needed no
    `reference_date` field whatsoever. Unlike that case, one rule here
    genuinely does need it (checking staleness inherently requires an
    external "now" a bounded history alone cannot supply), so the field
    exists — see
    `docs/adr/0019-progress-evaluation-consistency-and-plateau-scope.md`.
    """

    progress_history: tuple[ProgressContext, ...]
    goal: GoalContext | None = None
    reference_date: date

    @classmethod
    def from_snapshots(
        cls,
        *,
        progress_history: Sequence[ProgressContext],
        goal: GoalContext | None = None,
        reference_date: date,
    ) -> ProgressEvaluationRuleContext:
        """Builds a context from already-built snapshots, sorted
        chronologically — the primary constructor path once a caller
        already has `ProgressContext` values (and, optionally, a
        `GoalContext`) in hand; this package performs no repository
        lookups of its own."""
        ordered = sorted(progress_history, key=lambda entry: entry.progress_date.value)
        return cls(progress_history=tuple(ordered), goal=goal, reference_date=reference_date)

    @classmethod
    def from_aggregates(
        cls,
        *,
        progress_records: Sequence[Progress],
        goal: Goal | None,
        clock: Clock,
    ) -> ProgressEvaluationRuleContext:
        """Convenience path from live aggregates: snapshots each
        `Progress` via `ProgressContext.from_progress()`, the goal (if
        any) via `GoalContext.from_goal()`, and stamps `reference_date`
        from `clock.now().date()` — the same "caller supplies a `Clock`,
        never reads the system clock directly" discipline
        `GoalAlignmentRuleContext.from_aggregates()` already follows.
        """
        return cls.from_snapshots(
            progress_history=[ProgressContext.from_progress(record) for record in progress_records],
            goal=GoalContext.from_goal(goal) if goal is not None else None,
            reference_date=clock.now().date(),
        )
