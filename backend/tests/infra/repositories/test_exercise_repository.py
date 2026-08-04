"""Integration tests for `ExerciseSqlRepository` against a real, migrated
Postgres database. See `test_user_repository.py`'s module docstring for the
shared fixture convention.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.domain.exercise.enums import Difficulty, ExerciseStatus, MovementPattern
from app.domain.exercise.exercise import Exercise
from app.domain.exercise.identifiers import ExerciseId
from app.domain.exercise.value_objects import (
    EquipmentRequirement,
    ExerciseInstructions,
    ExerciseName,
    PrimaryMuscle,
)
from app.domain.shared_kernel.clock import FixedClock
from app.infra.repositories.exercise_repository import ExerciseSqlRepository

_CLOCK = FixedClock(datetime(2026, 1, 1, tzinfo=timezone.utc))


@pytest.mark.integration
def test_add_and_get_round_trip(session_factory: sessionmaker[Session]) -> None:
    exercise_id = ExerciseId.generate()
    exercise = Exercise.create(
        exercise_id=exercise_id,
        name=ExerciseName("Barbell Bench Press"),
        movement_pattern=MovementPattern.PUSH,
        difficulty=Difficulty.INTERMEDIATE,
        instructions=ExerciseInstructions("Lie on a bench, lower the bar, press up."),
        primary_muscles=(PrimaryMuscle("chest"),),
        equipment_requirements=frozenset(
            {EquipmentRequirement("barbell"), EquipmentRequirement("bench")}
        ),
        clock=_CLOCK,
    )

    with session_factory() as session:
        ExerciseSqlRepository(session).add(exercise)
        session.commit()

    with session_factory() as session:
        fetched = ExerciseSqlRepository(session).get(exercise_id)

    assert fetched is not None
    assert fetched.name == ExerciseName("Barbell Bench Press")
    assert fetched.movement_pattern is MovementPattern.PUSH
    assert fetched.primary_muscles == (PrimaryMuscle("chest"),)
    assert fetched.equipment_requirements == frozenset(
        {EquipmentRequirement("barbell"), EquipmentRequirement("bench")}
    )
    assert fetched.status is ExerciseStatus.ACTIVE


@pytest.mark.integration
def test_mutation_persists_without_a_second_add_call(
    session_factory: sessionmaker[Session],
) -> None:
    exercise_id = ExerciseId.generate()
    exercise = Exercise.create(
        exercise_id=exercise_id,
        name=ExerciseName("Squat"),
        movement_pattern=MovementPattern.SQUAT,
        difficulty=Difficulty.BEGINNER,
        instructions=ExerciseInstructions("Bend the knees and hips, then stand back up."),
        clock=_CLOCK,
    )

    with session_factory() as session:
        ExerciseSqlRepository(session).add(exercise)
        session.commit()

    with session_factory() as session:
        repository = ExerciseSqlRepository(session)
        fetched = repository.get(exercise_id)
        assert fetched is not None
        fetched.deprecate(clock=_CLOCK)
        session.commit()

    with session_factory() as session:
        refetched = ExerciseSqlRepository(session).get(exercise_id)

    assert refetched is not None
    assert refetched.status is ExerciseStatus.DEPRECATED


@pytest.mark.integration
def test_remove_deletes_the_row(session_factory: sessionmaker[Session]) -> None:
    exercise_id = ExerciseId.generate()
    exercise = Exercise.create(
        exercise_id=exercise_id,
        name=ExerciseName("Deadlift"),
        movement_pattern=MovementPattern.HINGE,
        difficulty=Difficulty.ADVANCED,
        instructions=ExerciseInstructions("Hinge at the hips and lift the bar."),
        clock=_CLOCK,
    )

    with session_factory() as session:
        repository = ExerciseSqlRepository(session)
        repository.add(exercise)
        session.commit()
        repository.remove(exercise)
        session.commit()

    with session_factory() as session:
        assert ExerciseSqlRepository(session).get(exercise_id) is None
