"""Tests for app/domain/workout_session/exercise_performance.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.workout_session.exercise_performance import ExercisePerformance, PerformanceNotes
from app.domain.workout_session.identifiers import ExercisePerformanceId
from tests.domain.workout_session.factories import an_exercise_id, an_exercise_set

# --- PerformanceNotes ---


@pytest.mark.unit
def test_performance_notes_defaults_to_empty() -> None:
    assert PerformanceNotes().value == ""


@pytest.mark.unit
def test_performance_notes_accepts_an_explicitly_empty_value() -> None:
    assert PerformanceNotes("").value == ""


@pytest.mark.unit
def test_performance_notes_accepts_a_non_empty_value() -> None:
    assert PerformanceNotes("Left knee felt off.").value == "Left knee felt off."


@pytest.mark.unit
def test_performance_notes_rejects_an_overly_long_value() -> None:
    with pytest.raises(DomainInvariantViolationError, match="at most 2000 characters"):
        PerformanceNotes("x" * 2001)


@pytest.mark.unit
def test_performance_notes_is_immutable() -> None:
    notes = PerformanceNotes("Felt strong.")
    with pytest.raises(FrozenInstanceError):
        notes.value = "Changed"  # type: ignore[misc]


# --- ExercisePerformance construction ---


@pytest.mark.unit
def test_construction_defaults_to_empty_notes_and_no_sets() -> None:
    performance = ExercisePerformance(
        ExercisePerformanceId.generate(), exercise_id=an_exercise_id()
    )
    assert performance.notes == PerformanceNotes()
    assert performance.sets == ()


@pytest.mark.unit
def test_construction_exposes_the_exercise_id_it_was_given() -> None:
    exercise_id = an_exercise_id()
    performance = ExercisePerformance(ExercisePerformanceId.generate(), exercise_id=exercise_id)
    assert performance.exercise_id == exercise_id


@pytest.mark.unit
def test_construction_accepts_explicit_notes_and_sets() -> None:
    notes = PerformanceNotes("Great pump.")
    sets = (an_exercise_set(set_number=1),)
    performance = ExercisePerformance(
        ExercisePerformanceId.generate(), exercise_id=an_exercise_id(), notes=notes, sets=sets
    )
    assert performance.notes == notes
    assert performance.sets == sets


@pytest.mark.unit
def test_equality_is_by_identity_not_field_values() -> None:
    """`ExercisePerformance` is an Entity — two performances with the same
    exercise_id/notes/sets but different ids are not equal, unlike a value
    object."""
    exercise_id = an_exercise_id()
    first = ExercisePerformance(ExercisePerformanceId.generate(), exercise_id=exercise_id)
    second = ExercisePerformance(ExercisePerformanceId.generate(), exercise_id=exercise_id)
    assert first != second


# --- add_set() ---


@pytest.mark.unit
def test_add_set_appends_to_the_ordered_tuple() -> None:
    performance = ExercisePerformance(
        ExercisePerformanceId.generate(), exercise_id=an_exercise_id()
    )
    first_set = an_exercise_set(set_number=1)
    second_set = an_exercise_set(set_number=2)

    performance.add_set(first_set)
    performance.add_set(second_set)

    assert performance.sets == (first_set, second_set)


@pytest.mark.unit
def test_add_set_preserves_insertion_order_even_when_set_numbers_are_out_of_order() -> None:
    """ "Ordering of sets must be preserved" means insertion order, not
    ascending set_number order."""
    performance = ExercisePerformance(
        ExercisePerformanceId.generate(), exercise_id=an_exercise_id()
    )
    set_three = an_exercise_set(set_number=3)
    set_one = an_exercise_set(set_number=1)

    performance.add_set(set_three)
    performance.add_set(set_one)

    assert performance.sets == (set_three, set_one)


@pytest.mark.unit
def test_add_set_rejects_a_duplicate_set_number() -> None:
    performance = ExercisePerformance(
        ExercisePerformanceId.generate(), exercise_id=an_exercise_id()
    )
    performance.add_set(an_exercise_set(set_number=1, weight=100.0))

    with pytest.raises(DomainInvariantViolationError, match="duplicate set number"):
        performance.add_set(an_exercise_set(set_number=1, weight=110.0))


# --- complete_set() ---


@pytest.mark.unit
def test_complete_set_marks_the_matching_set_complete() -> None:
    performance = ExercisePerformance(
        ExercisePerformanceId.generate(), exercise_id=an_exercise_id()
    )
    performance.add_set(an_exercise_set(set_number=1, completed=False))

    performance.complete_set(1)

    assert performance.sets[0].completed is True


@pytest.mark.unit
def test_complete_set_returns_the_newly_completed_set() -> None:
    performance = ExercisePerformance(
        ExercisePerformanceId.generate(), exercise_id=an_exercise_id()
    )
    performance.add_set(an_exercise_set(set_number=1, weight=100.0))

    completed = performance.complete_set(1)

    assert completed.completed is True
    assert completed.weight.value == 100.0


@pytest.mark.unit
def test_complete_set_preserves_position_within_the_ordered_tuple() -> None:
    performance = ExercisePerformance(
        ExercisePerformanceId.generate(), exercise_id=an_exercise_id()
    )
    performance.add_set(an_exercise_set(set_number=1))
    performance.add_set(an_exercise_set(set_number=2))
    performance.add_set(an_exercise_set(set_number=3))

    performance.complete_set(2)

    assert [s.set_number.value for s in performance.sets] == [1, 2, 3]
    assert performance.sets[1].completed is True
    assert performance.sets[0].completed is False
    assert performance.sets[2].completed is False


@pytest.mark.unit
def test_complete_set_raises_for_an_unknown_set_number() -> None:
    performance = ExercisePerformance(
        ExercisePerformanceId.generate(), exercise_id=an_exercise_id()
    )
    with pytest.raises(DomainInvariantViolationError, match="no set numbered"):
        performance.complete_set(1)


# --- update_notes() ---


@pytest.mark.unit
def test_update_notes_replaces_the_notes() -> None:
    performance = ExercisePerformance(
        ExercisePerformanceId.generate(), exercise_id=an_exercise_id()
    )
    performance.update_notes(PerformanceNotes("New note."))
    assert performance.notes == PerformanceNotes("New note.")
