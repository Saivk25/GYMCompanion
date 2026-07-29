"""`ExerciseSet`: one logged set within an `ExercisePerformance`.

A `ValueObject`, not an `Entity` — deliberately, unlike `ExercisePerformance`
(`exercise_performance.py`). Within one `ExercisePerformance`, "cannot
duplicate set numbers" already makes `set_number` a natural, unique key;
introducing a separate synthetic identity on top of that would add
machinery with nothing left for it to do. Marking a set complete
(`mark_completed()`) therefore doesn't mutate a set in place — it returns a
new `ExerciseSet` with `completed=True`, which `ExercisePerformance`
substitutes into its ordered list at the matching `set_number`. This is the
same "rich value object, replaced wholesale on change" discipline every
other value object in this codebase follows.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from app.domain.shared_kernel.validation import ensure
from app.domain.shared_kernel.value_object import ValueObject

# RPE shares its 1-10 bound and Borg CR10 rationale with
# `app.domain.workout_session.value_objects.SessionRating` (see that
# class's docstring) but is a genuinely different observation — "how hard
# did this specific set feel" versus "how did the whole session feel" — so
# it gets its own value object rather than reusing SessionRating for a
# different concept that happens to share a scale.
_MIN_RPE = 1
_MAX_RPE = 10


@dataclass(frozen=True)
class SetNumber(ValueObject):
    """This set's position within its `ExercisePerformance`, 1-based.
    "Set number > 0" is the only per-field rule; "cannot duplicate set
    numbers" is a cross-set invariant that only `ExercisePerformance` can
    see (the same reasoning `app.domain.exercise.exercise`'s muscle-overlap
    check documents), so it is enforced there, not here.
    """

    value: int

    def __post_init__(self) -> None:
        ensure(self.value > 0, f"set number must be positive, got {self.value}")


@dataclass(frozen=True)
class SetWeight(ValueObject):
    """The load used for this set. Zero is valid and common — a bodyweight
    set (push-ups, bodyweight squats, an unweighted pull-up) has genuinely
    no external load, which is a normal set to log, not an error. Only a
    negative weight is rejected.
    """

    value: float

    def __post_init__(self) -> None:
        ensure(self.value >= 0, f"set weight must not be negative, got {self.value}")


@dataclass(frozen=True)
class SetReps(ValueObject):
    """Repetitions completed. Strictly positive — a set with zero reps
    didn't happen, so there is nothing to log; a set the user didn't
    perform simply isn't added, rather than being added with `reps=0`.
    """

    value: int

    def __post_init__(self) -> None:
        ensure(self.value > 0, f"reps must be positive, got {self.value}")


@dataclass(frozen=True)
class SetRPE(ValueObject):
    """Rate of Perceived Exertion for this specific set, 1-10 — see the
    module-level comment above for why this is distinct from
    `SessionRating` despite sharing a scale."""

    value: int

    def __post_init__(self) -> None:
        ensure(
            _MIN_RPE <= self.value <= _MAX_RPE,
            f"RPE must be between {_MIN_RPE} and {_MAX_RPE}, got {self.value}",
        )


@dataclass(frozen=True)
class ExerciseSet(ValueObject):
    """One logged set: what was actually done, plus whether it's confirmed
    complete. `set_number`, `weight`, `reps`, and `rpe` are supplied
    together at logging time — this models "record what just happened",
    not a plan filled in progressively — while `completed` defaults to
    `False` and is flipped by `ExercisePerformance.complete_set()`, which
    is what the task's dedicated `ExerciseSetCompleted` event (as opposed
    to the general `ExercisePerformanceUpdated`) is for.
    """

    set_number: SetNumber
    weight: SetWeight
    reps: SetReps
    rpe: SetRPE
    completed: bool = False

    def mark_completed(self) -> ExerciseSet:
        """Returns a new `ExerciseSet` identical to this one except
        `completed=True`. A no-op-shaped call (marking an already-complete
        set complete again) is allowed here — `ExercisePerformance.
        complete_set()` is where "does this set exist" is enforced; this
        method has no way to check that on its own."""
        return replace(self, completed=True)
