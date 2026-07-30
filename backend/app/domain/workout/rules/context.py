"""`ProgressiveOverloadRuleContext`: the `RuleContext` (`app.domain.rules`)
subtype every progressive overload rule in this package evaluates against.

Unlike every prior phase's context, this one is inherently about *trends
across many sessions*, not one aggregate's (or two aggregates') fields at
a single point in time. Neither of `ReadinessRuleContext`'s/
`NutritionRuleContext`'s "flatten one aggregate's fields" shape nor
`GoalAlignmentRuleContext`'s "reference whole snapshots" shape (see
`docs/adr/0016-goal-alignment-combines-whole-snapshots.md`) fits a
history of sessions well — five rules each re-deriving the same
volume/load totals from raw `ExerciseSet` tuples on every evaluation
would duplicate that arithmetic five times over, with no shared place to
document the (real, and documented below) simplifications that arithmetic
involves.

Instead, this context holds a **pre-computed summary per session**
(`WorkoutSessionSummary`), built once via `from_session_contexts()` from
however many `WorkoutSessionContext` snapshots the caller supplies. This
is exactly the "historical summaries already supplied by the application
layer" option this phase's own task explicitly names — the summarizing
happens in this package (still framework-independent, still no
repository or service access), not in a hypothetical application-layer
module this phase does not build.

No wall-clock reads anywhere in this package: every trend, frequency, and
overload judgment below is computed purely from the `session_date`s and
logged sets already present in the supplied `WorkoutSessionContext`s —
there is no `reference_date` field here the way
`GoalAlignmentRuleContext` needed one, because nothing in this package
asks "how does this compare to today," only "how do these sessions
compare to each other."
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.rules.context import RuleContext
from app.domain.shared_kernel.validation import ensure
from app.domain.shared_kernel.value_object import ValueObject
from app.domain.workout_session.context import WorkoutSessionContext
from app.domain.workout_session.enums import SessionStatus
from app.domain.workout_session.value_objects import SessionDate


@dataclass(frozen=True, kw_only=True)
class WorkoutSessionSummary(ValueObject):
    """A deterministic, pre-computed summary of one Completed
    `WorkoutSession`'s training volume and load, so every rule in this
    package reads the same numbers rather than each recomputing totals
    independently from raw `ExerciseSet` tuples.

    Two documented simplifications, both whole-session, whole-program
    granularity rather than per-exercise:

    1. **Every logged `ExerciseSet` counts, regardless of its own
       `completed` flag.** `ExerciseSet.completed` marks a UI-level
       confirmation step (`ExercisePerformance.complete_set()`), not
       whether the set was actually performed — `weight`/`reps`/`rpe` are
       already supplied together at logging time, which is what "record
       what just happened" means (see `exercise_set.py`'s own module
       docstring). The owning `WorkoutSession.status` being `Completed`
       is this package's reliability gate for a session's data being
       finalized and safe to fold into a trend calculation — not the
       per-set `completed` flag.
    2. **`total_volume` and `average_load` are computed across every
       exercise in a session combined**, not per exercise. This mixes
       genuinely different movements' loads (a 15 kg dumbbell curl and a
       100 kg squat both contribute to the same session's "average
       load"), and `average_load` additionally blends weighted and
       bodyweight (zero-load, per `SetWeight`'s own "zero is valid"
       rule) sets uniformly — a session built mostly from bodyweight work
       will show a low `average_load` not because true intensity
       declined, but because the exercises selected don't use external
       load. Both are real, stated limitations, not silently assumed
       away: a future increment computing genuine per-exercise
       progression (e.g. against `Exercise`-scoped history, or a
       %1RM-normalized intensity measure) would need to replace this
       whole-session summary, not just adjust its thresholds. See
       `docs/adr/0017-progressive-overload-session-level-trends.md`.
    """

    session_date: SessionDate
    total_volume: float
    average_load: float | None
    logged_set_count: int

    @classmethod
    def from_session_context(cls, session: WorkoutSessionContext) -> WorkoutSessionSummary:
        """Builds a summary from one `WorkoutSessionContext` snapshot.
        Raises if the session is not `Completed` — see this package's
        `ProgressiveOverloadRuleContext.from_session_contexts()` for why
        only Completed sessions are meaningful trend evidence; this
        method enforces that invariant defensively even if called
        directly.
        """
        ensure(
            session.status is SessionStatus.COMPLETED,
            "a WorkoutSessionSummary can only be computed from a Completed WorkoutSession, "
            f"got status {session.status.value!r}",
        )
        sets = [
            exercise_set
            for performance in session.exercise_performances
            for exercise_set in performance.sets
        ]
        total_volume = sum(
            exercise_set.weight.value * exercise_set.reps.value for exercise_set in sets
        )
        average_load = (
            sum(exercise_set.weight.value for exercise_set in sets) / len(sets) if sets else None
        )
        return cls(
            session_date=session.session_date,
            total_volume=total_volume,
            average_load=average_load,
            logged_set_count=len(sets),
        )


@dataclass(frozen=True, kw_only=True)
class ProgressiveOverloadRuleContext(RuleContext):
    """One evaluation's worth of progressive overload data: an ordered
    history of `WorkoutSessionSummary` values, oldest first.

    Direct construction (`ProgressiveOverloadRuleContext(sessions=...)`)
    trusts the caller to supply `sessions` already in chronological
    order — the same "caller-supplied, not re-derived" trust every other
    context in this codebase places in its inputs. `from_session_contexts()`
    below is the safer, primary construction path: it sorts by
    `session_date` itself and filters to `Completed` sessions only, so a
    caller handing over an unordered mix of session statuses still gets a
    context every rule in this package can rely on.
    """

    sessions: tuple[WorkoutSessionSummary, ...]

    @classmethod
    def from_session_contexts(
        cls, sessions: Sequence[WorkoutSessionContext]
    ) -> ProgressiveOverloadRuleContext:
        """Builds a context from however many `WorkoutSessionContext`
        snapshots the caller supplies, in any order and any mix of
        statuses. Only `Completed` sessions become trend evidence —
        `Planned`/`Active` sessions have not finished, and `Abandoned`
        sessions may hold only a partial record — either way, folding
        them into a volume or intensity trend would misrepresent what
        actually happened. Takes snapshots, not a repository or a
        `WorkoutSession` aggregate list — this package declares no
        repository or service dependency of its own; loading and
        snapshotting the sessions first is a caller concern.
        """
        completed = [session for session in sessions if session.status is SessionStatus.COMPLETED]
        ordered = sorted(completed, key=lambda session: session.session_date.value)
        return cls(
            sessions=tuple(
                WorkoutSessionSummary.from_session_context(session) for session in ordered
            )
        )
