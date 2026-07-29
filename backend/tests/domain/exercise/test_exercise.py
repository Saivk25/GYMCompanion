"""Tests for app/domain/exercise/exercise.py."""

from datetime import datetime, timezone

import pytest

from app.domain.exercise.enums import Difficulty, ExerciseStatus, MovementPattern
from app.domain.exercise.events import ExerciseCreated, ExerciseDeprecated, ExerciseUpdated
from app.domain.exercise.exercise import Exercise
from app.domain.exercise.identifiers import ExerciseId
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
from tests.domain.exercise.factories import a_created_exercise, a_fixed_clock

_INSTRUCTIONS = ExerciseInstructions("Lie on the bench, lower the bar, press up.")

# --- create() ---


@pytest.mark.unit
def test_create_starts_in_the_active_state() -> None:
    exercise = a_created_exercise()
    assert exercise.status == ExerciseStatus.ACTIVE


@pytest.mark.unit
def test_create_stamps_created_at_from_the_clock() -> None:
    clock = a_fixed_clock()
    exercise = Exercise.create(
        exercise_id=ExerciseId.generate(),
        name=ExerciseName("Barbell Bench Press"),
        movement_pattern=MovementPattern.PUSH,
        difficulty=Difficulty.INTERMEDIATE,
        instructions=_INSTRUCTIONS,
        clock=clock,
    )
    assert exercise.created_at == clock.now()


@pytest.mark.unit
def test_create_exposes_the_fields_it_was_given() -> None:
    exercise_id = ExerciseId.generate()
    exercise = Exercise.create(
        exercise_id=exercise_id,
        name=ExerciseName("Barbell Bench Press"),
        movement_pattern=MovementPattern.PUSH,
        difficulty=Difficulty.INTERMEDIATE,
        instructions=_INSTRUCTIONS,
        description=ExerciseDescription("A compound push movement."),
        primary_muscles=(PrimaryMuscle("chest"),),
        secondary_muscles=SecondaryMuscles(frozenset({"triceps"})),
        equipment_requirements=frozenset({EquipmentRequirement("barbell")}),
        contraindications=Contraindications(frozenset({"shoulder impingement"})),
        clock=a_fixed_clock(),
    )
    assert exercise.id == exercise_id
    assert exercise.name == ExerciseName("Barbell Bench Press")
    assert exercise.movement_pattern is MovementPattern.PUSH
    assert exercise.difficulty is Difficulty.INTERMEDIATE
    assert exercise.instructions == _INSTRUCTIONS
    assert exercise.description == ExerciseDescription("A compound push movement.")
    assert exercise.primary_muscles == (PrimaryMuscle("chest"),)
    assert exercise.secondary_muscles == SecondaryMuscles(frozenset({"triceps"}))
    assert exercise.equipment_requirements == frozenset({EquipmentRequirement("barbell")})
    assert exercise.contraindications == Contraindications(frozenset({"shoulder impingement"}))


@pytest.mark.unit
def test_create_defaults_to_no_description_no_muscles_no_equipment_no_contraindications() -> None:
    exercise = a_created_exercise()
    assert exercise.description is None
    assert exercise.primary_muscles == ()
    assert exercise.secondary_muscles == SecondaryMuscles()
    assert exercise.equipment_requirements == frozenset()
    assert exercise.contraindications == Contraindications()


@pytest.mark.unit
def test_create_starts_with_no_updated_at_or_deprecated_at() -> None:
    exercise = a_created_exercise()
    assert exercise.updated_at is None
    assert exercise.deprecated_at is None


@pytest.mark.unit
def test_create_records_an_exercise_created_event() -> None:
    clock = a_fixed_clock()
    exercise_id = ExerciseId.generate()
    exercise = Exercise.create(
        exercise_id=exercise_id,
        name=ExerciseName("Barbell Bench Press"),
        movement_pattern=MovementPattern.PUSH,
        difficulty=Difficulty.INTERMEDIATE,
        instructions=_INSTRUCTIONS,
        clock=clock,
    )

    events = exercise.pull_domain_events()

    assert len(events) == 1
    assert isinstance(events[0], ExerciseCreated)
    assert events[0].exercise_id == exercise_id
    assert events[0].name == ExerciseName("Barbell Bench Press")
    assert events[0].movement_pattern is MovementPattern.PUSH
    assert events[0].difficulty is Difficulty.INTERMEDIATE
    assert events[0].occurred_at == clock.now()


@pytest.mark.unit
def test_create_generates_a_distinct_exercise_each_time() -> None:
    assert a_created_exercise().id != a_created_exercise().id


# --- rule: exercise name cannot be empty ---


@pytest.mark.unit
def test_exercise_name_cannot_be_empty() -> None:
    with pytest.raises(DomainInvariantViolationError, match="exercise name must not be empty"):
        ExerciseName("")


# --- rule: instructions cannot be empty ---


@pytest.mark.unit
def test_instructions_cannot_be_empty() -> None:
    with pytest.raises(DomainInvariantViolationError, match="must not be empty"):
        ExerciseInstructions("")


# --- rule: movement pattern required / difficulty required ---


@pytest.mark.unit
def test_movement_pattern_is_required_by_the_type_system() -> None:
    """`movement_pattern` is a required, non-Optional constructor
    parameter — enforced statically by mypy for any real caller, the same
    approach `WorkoutDate` documents for "date must exist". Calling
    without it is a `TypeError` from Python itself, not a domain rule to
    test at runtime."""
    with pytest.raises(TypeError):
        Exercise.create(  # type: ignore[call-arg]
            exercise_id=ExerciseId.generate(),
            name=ExerciseName("Barbell Bench Press"),
            difficulty=Difficulty.INTERMEDIATE,
            instructions=_INSTRUCTIONS,
            clock=a_fixed_clock(),
        )


@pytest.mark.unit
def test_difficulty_is_required_by_the_type_system() -> None:
    with pytest.raises(TypeError):
        Exercise.create(  # type: ignore[call-arg]
            exercise_id=ExerciseId.generate(),
            name=ExerciseName("Barbell Bench Press"),
            movement_pattern=MovementPattern.PUSH,
            instructions=_INSTRUCTIONS,
            clock=a_fixed_clock(),
        )


# --- rule: no duplicate primary muscle ---


@pytest.mark.unit
def test_no_duplicate_primary_muscle_on_create() -> None:
    with pytest.raises(DomainInvariantViolationError, match="duplicate muscle"):
        Exercise.create(
            exercise_id=ExerciseId.generate(),
            name=ExerciseName("Barbell Bench Press"),
            movement_pattern=MovementPattern.PUSH,
            difficulty=Difficulty.INTERMEDIATE,
            instructions=_INSTRUCTIONS,
            primary_muscles=(PrimaryMuscle("chest"), PrimaryMuscle("chest")),
            clock=a_fixed_clock(),
        )


@pytest.mark.unit
def test_no_duplicate_primary_muscle_is_case_insensitive() -> None:
    with pytest.raises(DomainInvariantViolationError, match="duplicate muscle"):
        Exercise.create(
            exercise_id=ExerciseId.generate(),
            name=ExerciseName("Barbell Bench Press"),
            movement_pattern=MovementPattern.PUSH,
            difficulty=Difficulty.INTERMEDIATE,
            instructions=_INSTRUCTIONS,
            primary_muscles=(PrimaryMuscle("Chest"), PrimaryMuscle("chest")),
            clock=a_fixed_clock(),
        )


@pytest.mark.unit
def test_no_duplicate_primary_muscle_on_update() -> None:
    exercise = a_created_exercise()
    with pytest.raises(DomainInvariantViolationError, match="duplicate muscle"):
        exercise.update(
            primary_muscles=(PrimaryMuscle("chest"), PrimaryMuscle("chest")),
            clock=a_fixed_clock(),
        )


@pytest.mark.unit
def test_distinct_primary_muscles_are_accepted() -> None:
    exercise = Exercise.create(
        exercise_id=ExerciseId.generate(),
        name=ExerciseName("Barbell Bench Press"),
        movement_pattern=MovementPattern.PUSH,
        difficulty=Difficulty.INTERMEDIATE,
        instructions=_INSTRUCTIONS,
        primary_muscles=(PrimaryMuscle("chest"), PrimaryMuscle("triceps")),
        clock=a_fixed_clock(),
    )
    assert exercise.primary_muscles == (PrimaryMuscle("chest"), PrimaryMuscle("triceps"))


# --- rule: primary muscle cannot also appear as secondary ---


@pytest.mark.unit
def test_primary_muscle_cannot_also_appear_as_secondary_on_create() -> None:
    with pytest.raises(DomainInvariantViolationError, match="cannot be both primary and secondary"):
        Exercise.create(
            exercise_id=ExerciseId.generate(),
            name=ExerciseName("Barbell Bench Press"),
            movement_pattern=MovementPattern.PUSH,
            difficulty=Difficulty.INTERMEDIATE,
            instructions=_INSTRUCTIONS,
            primary_muscles=(PrimaryMuscle("chest"),),
            secondary_muscles=SecondaryMuscles(frozenset({"chest"})),
            clock=a_fixed_clock(),
        )


@pytest.mark.unit
def test_primary_muscle_cannot_also_appear_as_secondary_is_case_insensitive() -> None:
    with pytest.raises(DomainInvariantViolationError, match="cannot be both primary and secondary"):
        Exercise.create(
            exercise_id=ExerciseId.generate(),
            name=ExerciseName("Barbell Bench Press"),
            movement_pattern=MovementPattern.PUSH,
            difficulty=Difficulty.INTERMEDIATE,
            instructions=_INSTRUCTIONS,
            primary_muscles=(PrimaryMuscle("Chest"),),
            secondary_muscles=SecondaryMuscles(frozenset({"chest"})),
            clock=a_fixed_clock(),
        )


@pytest.mark.unit
def test_primary_muscle_cannot_also_appear_as_secondary_on_update() -> None:
    exercise = Exercise.create(
        exercise_id=ExerciseId.generate(),
        name=ExerciseName("Barbell Bench Press"),
        movement_pattern=MovementPattern.PUSH,
        difficulty=Difficulty.INTERMEDIATE,
        instructions=_INSTRUCTIONS,
        primary_muscles=(PrimaryMuscle("chest"),),
        clock=a_fixed_clock(),
    )
    with pytest.raises(DomainInvariantViolationError, match="cannot be both primary and secondary"):
        exercise.update(
            secondary_muscles=SecondaryMuscles(frozenset({"chest"})),
            clock=a_fixed_clock(),
        )


@pytest.mark.unit
def test_disjoint_primary_and_secondary_muscles_are_accepted() -> None:
    exercise = Exercise.create(
        exercise_id=ExerciseId.generate(),
        name=ExerciseName("Barbell Bench Press"),
        movement_pattern=MovementPattern.PUSH,
        difficulty=Difficulty.INTERMEDIATE,
        instructions=_INSTRUCTIONS,
        primary_muscles=(PrimaryMuscle("chest"),),
        secondary_muscles=SecondaryMuscles(frozenset({"triceps"})),
        clock=a_fixed_clock(),
    )
    assert exercise.primary_muscles == (PrimaryMuscle("chest"),)
    assert exercise.secondary_muscles == SecondaryMuscles(frozenset({"triceps"}))


# --- update() ---


@pytest.mark.unit
def test_update_replaces_only_the_given_fields() -> None:
    exercise = a_created_exercise()
    original_movement_pattern = exercise.movement_pattern

    exercise.update(name=ExerciseName("Incline Barbell Bench Press"), clock=a_fixed_clock())

    assert exercise.name == ExerciseName("Incline Barbell Bench Press")
    assert exercise.movement_pattern == original_movement_pattern


@pytest.mark.unit
def test_update_can_replace_description() -> None:
    exercise = a_created_exercise()
    exercise.update(description=ExerciseDescription("Updated description."), clock=a_fixed_clock())
    assert exercise.description == ExerciseDescription("Updated description.")


@pytest.mark.unit
def test_update_can_replace_movement_pattern() -> None:
    exercise = a_created_exercise()
    exercise.update(movement_pattern=MovementPattern.PULL, clock=a_fixed_clock())
    assert exercise.movement_pattern is MovementPattern.PULL


@pytest.mark.unit
def test_update_can_replace_difficulty() -> None:
    exercise = a_created_exercise()
    exercise.update(difficulty=Difficulty.ADVANCED, clock=a_fixed_clock())
    assert exercise.difficulty is Difficulty.ADVANCED


@pytest.mark.unit
def test_update_can_replace_instructions() -> None:
    exercise = a_created_exercise()
    new_instructions = ExerciseInstructions("Updated instructions.")
    exercise.update(instructions=new_instructions, clock=a_fixed_clock())
    assert exercise.instructions == new_instructions


@pytest.mark.unit
def test_update_can_replace_contraindications() -> None:
    exercise = a_created_exercise()
    new_contraindications = Contraindications(frozenset({"lower back pain"}))
    exercise.update(contraindications=new_contraindications, clock=a_fixed_clock())
    assert exercise.contraindications == new_contraindications


@pytest.mark.unit
def test_update_stamps_updated_at_from_the_clock() -> None:
    exercise = a_created_exercise()
    clock = a_fixed_clock()
    exercise.update(name=ExerciseName("Renamed"), clock=clock)
    assert exercise.updated_at == clock.now()


@pytest.mark.unit
def test_update_records_an_exercise_updated_event_with_the_current_name() -> None:
    exercise = a_created_exercise()
    exercise.pull_domain_events()  # drain ExerciseCreated from setup
    clock = a_fixed_clock()

    exercise.update(name=ExerciseName("Renamed"), clock=clock)

    events = exercise.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], ExerciseUpdated)
    assert events[0].exercise_id == exercise.id
    assert events[0].name == ExerciseName("Renamed")
    assert events[0].occurred_at == clock.now()


@pytest.mark.unit
def test_update_with_no_arguments_still_records_an_event_with_the_unchanged_name() -> None:
    exercise = a_created_exercise()
    exercise.pull_domain_events()

    exercise.update(clock=a_fixed_clock())

    events = exercise.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], ExerciseUpdated)
    assert events[0].name == exercise.name


# --- rule: deprecated exercises cannot be modified ---


@pytest.mark.unit
def test_deprecated_exercise_cannot_be_updated() -> None:
    exercise = a_created_exercise()
    exercise.deprecate(clock=a_fixed_clock())

    with pytest.raises(DomainInvariantViolationError, match="cannot modify an exercise"):
        exercise.update(name=ExerciseName("Renamed"), clock=a_fixed_clock())


# --- deprecate() ---


@pytest.mark.unit
def test_deprecate_moves_active_to_deprecated() -> None:
    exercise = a_created_exercise()
    exercise.deprecate(clock=a_fixed_clock())
    assert exercise.status == ExerciseStatus.DEPRECATED


@pytest.mark.unit
def test_deprecate_stamps_deprecated_at_from_the_clock() -> None:
    exercise = a_created_exercise()
    clock = a_fixed_clock()
    exercise.deprecate(clock=clock)
    assert exercise.deprecated_at == clock.now()


@pytest.mark.unit
def test_deprecate_records_an_exercise_deprecated_event() -> None:
    exercise = a_created_exercise()
    exercise.pull_domain_events()  # drain ExerciseCreated from setup
    clock = a_fixed_clock()

    exercise.deprecate(clock=clock)

    events = exercise.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], ExerciseDeprecated)
    assert events[0].exercise_id == exercise.id
    assert events[0].occurred_at == clock.now()


@pytest.mark.unit
def test_cannot_deprecate_an_already_deprecated_exercise() -> None:
    exercise = a_created_exercise()
    exercise.deprecate(clock=a_fixed_clock())
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        exercise.deprecate(clock=a_fixed_clock())


# --- __init__ construction (repository rehydration path) ---


@pytest.mark.unit
def test_constructor_rejects_a_naive_created_at() -> None:
    with pytest.raises(DomainInvariantViolationError, match="timezone-aware"):
        Exercise(
            ExerciseId.generate(),
            name=ExerciseName("Barbell Bench Press"),
            movement_pattern=MovementPattern.PUSH,
            difficulty=Difficulty.INTERMEDIATE,
            instructions=_INSTRUCTIONS,
            created_at=datetime(2026, 1, 1),  # deliberately naive
        )


@pytest.mark.unit
def test_constructor_rehydrates_an_existing_exercise_without_raising_an_event() -> None:
    """The path a repository uses to reconstruct an Exercise already in
    storage — re-raising ExerciseCreated here would be wrong."""
    exercise = Exercise(
        ExerciseId.generate(),
        name=ExerciseName("Barbell Bench Press"),
        movement_pattern=MovementPattern.PUSH,
        difficulty=Difficulty.INTERMEDIATE,
        instructions=_INSTRUCTIONS,
        created_at=datetime.now(timezone.utc),
        status=ExerciseStatus.DEPRECATED,
    )
    assert exercise.pull_domain_events() == []
    assert exercise.status == ExerciseStatus.DEPRECATED


@pytest.mark.unit
def test_constructor_enforces_the_muscle_overlap_invariant_too() -> None:
    """Rehydration is not a bypass for the aggregate's own invariants —
    a corrupt row should fail loudly, not load silently invalid."""
    with pytest.raises(DomainInvariantViolationError, match="cannot be both primary and secondary"):
        Exercise(
            ExerciseId.generate(),
            name=ExerciseName("Barbell Bench Press"),
            movement_pattern=MovementPattern.PUSH,
            difficulty=Difficulty.INTERMEDIATE,
            instructions=_INSTRUCTIONS,
            created_at=datetime.now(timezone.utc),
            primary_muscles=(PrimaryMuscle("chest"),),
            secondary_muscles=SecondaryMuscles(frozenset({"chest"})),
        )
