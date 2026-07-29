"""Tests for app/domain/exercise/value_objects.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.exercise.value_objects import (
    Contraindications,
    EquipmentRequirement,
    ExerciseDescription,
    ExerciseInstructions,
    ExerciseName,
    PrimaryMuscle,
    SecondaryMuscles,
)
from app.domain.shared_kernel.errors import DomainInvariantViolationError

# --- ExerciseName ---


@pytest.mark.unit
def test_exercise_name_accepts_a_non_empty_value() -> None:
    assert ExerciseName("Barbell Bench Press").value == "Barbell Bench Press"


@pytest.mark.unit
def test_exercise_name_rejects_blank_values() -> None:
    with pytest.raises(DomainInvariantViolationError, match="exercise name must not be empty"):
        ExerciseName("   ")


@pytest.mark.unit
def test_exercise_name_rejects_an_overly_long_value() -> None:
    with pytest.raises(DomainInvariantViolationError, match="at most 200 characters"):
        ExerciseName("x" * 201)


@pytest.mark.unit
def test_exercise_name_is_immutable() -> None:
    name = ExerciseName("Barbell Bench Press")
    with pytest.raises(FrozenInstanceError):
        name.value = "Something Else"  # type: ignore[misc]


# --- ExerciseDescription ---


@pytest.mark.unit
def test_exercise_description_accepts_a_non_empty_value() -> None:
    assert ExerciseDescription("A compound push movement.").value == "A compound push movement."


@pytest.mark.unit
def test_exercise_description_rejects_blank_values() -> None:
    with pytest.raises(DomainInvariantViolationError, match="must not be empty"):
        ExerciseDescription("")


@pytest.mark.unit
def test_exercise_description_rejects_an_overly_long_value() -> None:
    with pytest.raises(DomainInvariantViolationError, match="at most 1000 characters"):
        ExerciseDescription("x" * 1001)


# --- ExerciseInstructions ---


@pytest.mark.unit
def test_exercise_instructions_accepts_a_non_empty_value() -> None:
    text = "Lie on the bench, lower the bar, press up."
    assert ExerciseInstructions(text).value == text


@pytest.mark.unit
def test_exercise_instructions_rejects_blank_values() -> None:
    with pytest.raises(DomainInvariantViolationError, match="must not be empty"):
        ExerciseInstructions("")


@pytest.mark.unit
def test_exercise_instructions_rejects_an_overly_long_value() -> None:
    with pytest.raises(DomainInvariantViolationError, match="at most 5000 characters"):
        ExerciseInstructions("x" * 5001)


# --- EquipmentRequirement ---


@pytest.mark.unit
def test_equipment_requirement_normalizes_casing_and_whitespace() -> None:
    assert EquipmentRequirement("  Barbell  ").value == "barbell"


@pytest.mark.unit
def test_equipment_requirement_rejects_blank_values() -> None:
    with pytest.raises(DomainInvariantViolationError, match="must not be empty"):
        EquipmentRequirement("   ")


@pytest.mark.unit
def test_equipment_requirement_rejects_an_overly_long_value() -> None:
    with pytest.raises(DomainInvariantViolationError, match="at most 100 characters"):
        EquipmentRequirement("x" * 101)


@pytest.mark.unit
def test_equipment_requirement_is_hashable_and_usable_in_a_frozenset() -> None:
    assert len({EquipmentRequirement("barbell"), EquipmentRequirement("Barbell")}) == 1


# --- PrimaryMuscle ---


@pytest.mark.unit
def test_primary_muscle_normalizes_casing_and_whitespace() -> None:
    assert PrimaryMuscle("  Chest  ").value == "chest"


@pytest.mark.unit
def test_primary_muscle_rejects_blank_values() -> None:
    with pytest.raises(DomainInvariantViolationError, match="must not be empty"):
        PrimaryMuscle("")


@pytest.mark.unit
def test_primary_muscle_rejects_an_overly_long_value() -> None:
    with pytest.raises(DomainInvariantViolationError, match="at most 100 characters"):
        PrimaryMuscle("x" * 101)


@pytest.mark.unit
def test_primary_muscle_equality_and_hash_are_case_insensitive() -> None:
    assert PrimaryMuscle("Chest") == PrimaryMuscle("chest")
    assert hash(PrimaryMuscle("Chest")) == hash(PrimaryMuscle("chest"))


# --- SecondaryMuscles ---


@pytest.mark.unit
def test_secondary_muscles_defaults_to_empty() -> None:
    assert SecondaryMuscles().values == frozenset()


@pytest.mark.unit
def test_secondary_muscles_normalizes_every_entry() -> None:
    muscles = SecondaryMuscles(frozenset({"Triceps", " Front Delts "}))
    assert muscles.values == frozenset({"triceps", "front delts"})


@pytest.mark.unit
def test_secondary_muscles_collapses_case_insensitive_duplicates() -> None:
    """Not an error here (contrast Exercise.primary_muscles' explicit
    duplicate rejection) — see the class docstring for why."""
    muscles = SecondaryMuscles(frozenset({"Triceps", "triceps"}))
    assert muscles.values == frozenset({"triceps"})


@pytest.mark.unit
def test_secondary_muscles_rejects_a_blank_entry() -> None:
    with pytest.raises(DomainInvariantViolationError, match="must not be empty"):
        SecondaryMuscles(frozenset({""}))


@pytest.mark.unit
def test_secondary_muscles_rejects_an_overly_long_entry() -> None:
    with pytest.raises(DomainInvariantViolationError, match="at most 100 characters"):
        SecondaryMuscles(frozenset({"x" * 101}))


@pytest.mark.unit
def test_secondary_muscles_is_immutable() -> None:
    muscles = SecondaryMuscles(frozenset({"triceps"}))
    with pytest.raises(FrozenInstanceError):
        muscles.values = frozenset()  # type: ignore[misc]


# --- Contraindications ---


@pytest.mark.unit
def test_contraindications_defaults_to_empty() -> None:
    assert Contraindications().tags == frozenset()


@pytest.mark.unit
def test_contraindications_normalizes_every_tag() -> None:
    contraindications = Contraindications(frozenset({"Shoulder Impingement"}))
    assert contraindications.tags == frozenset({"shoulder impingement"})


@pytest.mark.unit
def test_contraindications_rejects_a_blank_tag() -> None:
    with pytest.raises(DomainInvariantViolationError, match="must not be empty"):
        Contraindications(frozenset({""}))


@pytest.mark.unit
def test_contraindications_rejects_an_overly_long_tag() -> None:
    with pytest.raises(DomainInvariantViolationError, match="at most 100 characters"):
        Contraindications(frozenset({"x" * 101}))


@pytest.mark.unit
def test_contraindications_is_immutable() -> None:
    contraindications = Contraindications(frozenset({"shoulder impingement"}))
    with pytest.raises(FrozenInstanceError):
        contraindications.tags = frozenset()  # type: ignore[misc]
