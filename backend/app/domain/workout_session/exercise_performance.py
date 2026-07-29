"""`ExercisePerformance`: what a user actually did for one exercise during
one `WorkoutSession`.

An `Entity` (`app.domain.shared_kernel.entity`), not a `ValueObject` and not
a second aggregate root — see
`docs/adr/0009-exercise-performance-owned-entity.md` for the full reasoning.
In short: it needs identity (to be added, removed, and targeted by later
operations independently of its field values — two performances of the
same exercise with identical sets so far are still two different
performances), but it is only ever created, changed, and persisted as part
of its owning `WorkoutSession`, never loaded or saved on its own. No
`ExercisePerformanceRepository` exists, and none should be added.

References `Exercise` by id only (`exercise_id: ExerciseId`), never by
object reference — the same cross-aggregate discipline
`WorkoutSession.workout_id`/`user_id` already establish. This module does
not import `app.domain.exercise` at all beyond the identifier type; no
repository lookup is performed or implied.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.exercise.identifiers import ExerciseId
from app.domain.shared_kernel.entity import Entity
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.validation import ensure
from app.domain.shared_kernel.value_object import ValueObject
from app.domain.workout_session.exercise_set import ExerciseSet
from app.domain.workout_session.identifiers import ExercisePerformanceId

_MAX_PERFORMANCE_NOTES_LENGTH = 2000


@dataclass(frozen=True)
class PerformanceNotes(ValueObject):
    """Free-text notes on one exercise's performance within a session
    (e.g. "left knee felt off on the last set") — distinct from
    `app.domain.workout_session.value_objects.SessionNotes`, which is
    about the session as a whole. Same "empty is a valid value, not
    `None`" discipline as `SessionNotes`, for the same reason: a
    performance always has notes, possibly empty, never a missing value
    object.
    """

    value: str = ""

    def __post_init__(self) -> None:
        ensure(
            len(self.value) <= _MAX_PERFORMANCE_NOTES_LENGTH,
            f"performance notes must be at most {_MAX_PERFORMANCE_NOTES_LENGTH} "
            f"characters, got {len(self.value)}",
        )


class ExercisePerformance(Entity[ExercisePerformanceId]):
    """One exercise's worth of logged sets within a `WorkoutSession`. See
    the module docstring for why this is an entity, not a value object or
    a second aggregate.

    Constructed only through `WorkoutSession.add_exercise(...)` — never
    directly by application code — so that the owning session can enforce
    "cannot modify once Completed or Abandoned" before delegating to this
    entity's own methods. Nothing in this class knows its owning session's
    status; see the class docstring in `workout_session.py` for why that
    guard lives there instead.
    """

    def __init__(
        self,
        performance_id: ExercisePerformanceId,
        *,
        exercise_id: ExerciseId,
        notes: PerformanceNotes | None = None,
        sets: tuple[ExerciseSet, ...] = (),
    ) -> None:
        super().__init__(performance_id)
        self._exercise_id = exercise_id
        self._notes = notes if notes is not None else PerformanceNotes()
        self._sets = sets

    @property
    def exercise_id(self) -> ExerciseId:
        return self._exercise_id

    @property
    def notes(self) -> PerformanceNotes:
        return self._notes

    @property
    def sets(self) -> tuple[ExerciseSet, ...]:
        """Every logged set, in the order they were added — "ordering of
        sets must be preserved" is satisfied structurally: sets are only
        ever appended, never reordered, so insertion order and read order
        are always the same tuple order."""
        return self._sets

    def add_set(self, exercise_set: ExerciseSet) -> None:
        """Appends a newly logged set. Rejects a duplicate `set_number` —
        the one cross-set invariant no single `ExerciseSet` value object
        can check on its own, so it lives here, the same reasoning
        `app.domain.exercise.exercise`'s muscle-overlap check documents
        for its own aggregate.
        """
        ensure(
            all(existing.set_number != exercise_set.set_number for existing in self._sets),
            f"duplicate set number: {exercise_set.set_number.value}",
        )
        self._sets = (*self._sets, exercise_set)

    def complete_set(self, set_number: int) -> ExerciseSet:
        """Marks the set with the given `set_number` complete, replacing it
        in place within the ordered tuple (position is preserved). Returns
        the newly completed `ExerciseSet` so the caller (`WorkoutSession.
        complete_set()`) can put it on the `ExerciseSetCompleted` event
        without looking it up a second time.
        """
        for index, existing in enumerate(self._sets):
            if existing.set_number.value == set_number:
                completed_set = existing.mark_completed()
                self._sets = (*self._sets[:index], completed_set, *self._sets[index + 1 :])
                return completed_set
        raise DomainInvariantViolationError(f"no set numbered {set_number} on this performance")

    def update_notes(self, notes: PerformanceNotes) -> None:
        self._notes = notes
