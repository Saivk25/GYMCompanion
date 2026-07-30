"""`TrainingLoadRuleContext`: the `RuleContext` (`app.domain.rules`)
subtype every training load rule in this package evaluates against.

Unlike `ProgressiveOverloadRuleContext`
(`app.domain.workout.rules.context`), which derives its own
`WorkoutSessionSummary` values from raw `WorkoutSessionContext`
snapshots via `from_session_contexts()`, this phase's own task is
explicit that "the application layer is responsible for preparing the
summaries" — this package declares no derivation method of its own,
only a value object shape the caller is trusted to have already
computed correctly. See
`docs/adr/0020-training-load-supplied-summaries.md` for why this is a
deliberate divergence from Progressive Overload's pattern, not an
oversight.

A `TrainingLoadSummary` is one day's worth of *already-computed*
training load — a single opaque, non-negative scalar
(`TrainingLoadSummary.load`) the caller derived using whatever formula
fits its data (e.g. session-RPE x duration ["sRPE load", Foster et al.
1995/2001], `WorkoutSessionSummary.total_volume`, or a wearable-
reported training-load metric). This package does not know or care
which formula produced the number — it only knows the number is
comparable day-to-day and summable into acute/chronic windows, the
same trust `Rule`'s own docstring already places in every other
context's supplied fields.

No wall-clock reads anywhere in this package, the same discipline
`ProgressiveOverloadRuleContext`'s own docstring establishes: every
acute and chronic window below is anchored to the *latest supplied
entry's* date via `trailing_window()`, never to `Clock`/today — there
is no `reference_date` field here, because nothing in this package
asks "how does this compare to today," only "how does this window
compare to the rest of the supplied history."
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta

from app.domain.rules.context import RuleContext
from app.domain.shared_kernel.validation import ensure
from app.domain.shared_kernel.value_object import ValueObject


@dataclass(frozen=True)
class TrainingLoadDate(ValueObject):
    """The calendar date one `TrainingLoadSummary` represents — a
    `datetime.date`, not a `datetime`, the same reasoning every other
    `*Date` value object in this codebase documents: a day's training
    load belongs to a day, not an instant.
    """

    value: date


@dataclass(frozen=True)
class TrainingLoad(ValueObject):
    """One day's already-computed training load, as a single
    non-negative scalar. "Training load must not be negative" — zero is
    a completely ordinary value (a rest day), the same `>= 0` (not
    `> 0`) reasoning `app.domain.nutrition.value_objects` documents for
    calories/protein/etc., not the strictly-positive reasoning
    `app.domain.progress.value_objects`'s body-measurement types use.
    """

    value: float

    def __post_init__(self) -> None:
        ensure(self.value >= 0, f"training load must not be negative, got {self.value}")


@dataclass(frozen=True, kw_only=True)
class TrainingLoadSummary(ValueObject):
    """One day's pre-computed training load, exactly as supplied by the
    application layer — this package performs no derivation of its own.
    See this module's own docstring for why.
    """

    load_date: TrainingLoadDate
    load: TrainingLoad


@dataclass(frozen=True, kw_only=True)
class TrainingLoadRuleContext(RuleContext):
    """One evaluation's worth of training load data: an ordered history
    of `TrainingLoadSummary` values, oldest first.

    Direct construction (`TrainingLoadRuleContext(history=...)`) trusts
    the caller to supply `history` already in chronological order — the
    same "caller-supplied, not re-derived" trust every other context in
    this codebase places in its inputs. `from_summaries()` below is the
    safer, primary construction path: it sorts by `load_date` itself, so
    a caller handing over an unordered list of summaries still gets a
    context every rule in this package can rely on.
    """

    history: tuple[TrainingLoadSummary, ...]

    @classmethod
    def from_summaries(cls, history: Sequence[TrainingLoadSummary]) -> TrainingLoadRuleContext:
        """Builds a context from however many `TrainingLoadSummary`
        values the caller supplies, in any order. Does not deduplicate
        same-date entries or fill gaps for missing days — both are
        application-layer concerns; this package only sorts what it is
        given.
        """
        ordered = sorted(history, key=lambda summary: summary.load_date.value)
        return cls(history=tuple(ordered))

    def trailing_window(self, *, window_days: int) -> tuple[TrainingLoadSummary, ...]:
        """Returns every summary whose `load_date` falls within the
        trailing `window_days`-day window ending at the latest supplied
        entry's date (inclusive on both ends) — e.g. `window_days=7`
        with a latest entry of 2026-01-28 returns every entry from
        2026-01-22 through 2026-01-28 inclusive.

        Anchored to the latest *supplied* entry, never to today
        (`Clock`) — see this module's own docstring on why this package
        reads no wall clock. Returns an empty tuple when `history` is
        empty. Every rule in this package builds its acute/chronic
        windows through this one method, so the windowing logic is
        defined and tested in exactly one place.
        """
        if not self.history:
            return ()
        latest = self.history[-1].load_date.value
        earliest_included = latest - timedelta(days=window_days - 1)
        return tuple(
            summary
            for summary in self.history
            if earliest_included <= summary.load_date.value <= latest
        )
