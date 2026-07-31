"""Tests for app/application/workout/dto/workout_session_dto.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.workout.dto.workout_session_dto import (
    ExercisePerformanceDTO,
    WorkoutSessionDTO,
)
from app.domain.exercise.identifiers import ExerciseId
from app.domain.workout_session.enums import SessionStatus
from tests.application.workout.factories import a_fixed_clock, a_planned_session


def an_exercise_id() -> ExerciseId:
    return ExerciseId.generate()


@pytest.mark.unit
def test_from_workout_session_maps_every_field_for_a_planned_session() -> None:
    session = a_planned_session()

    dto = WorkoutSessionDTO.from_workout_session(session)

    assert dto.session_id == session.id
    assert dto.workout_id == session.workout_id
    assert dto.user_id == session.user_id
    assert dto.status == SessionStatus.PLANNED
    assert dto.session_date == session.session_date
    assert dto.planned_at == session.planned_at
    assert dto.notes == session.notes
    assert dto.duration is None
    assert dto.completion_percentage is None
    assert dto.rating is None
    assert dto.started_at is None
    assert dto.completed_at is None
    assert dto.abandoned_at is None
    assert dto.exercise_performances == ()


@pytest.mark.unit
def test_from_workout_session_maps_exercise_performances() -> None:
    session = a_planned_session()
    session.start(clock=a_fixed_clock())
    exercise_id = an_exercise_id()
    performance_id = session.add_exercise(exercise_id, clock=a_fixed_clock())

    dto = WorkoutSessionDTO.from_workout_session(session)

    assert len(dto.exercise_performances) == 1
    performance_dto = dto.exercise_performances[0]
    assert isinstance(performance_dto, ExercisePerformanceDTO)
    assert performance_dto.performance_id == performance_id
    assert performance_dto.exercise_id == exercise_id
    assert performance_dto.sets == ()


@pytest.mark.unit
def test_workout_session_dto_is_immutable() -> None:
    dto = WorkoutSessionDTO.from_workout_session(a_planned_session())
    with pytest.raises(FrozenInstanceError):
        dto.status = SessionStatus.ACTIVE  # type: ignore[misc]


@pytest.mark.unit
def test_exercise_performance_dto_is_immutable() -> None:
    session = a_planned_session()
    session.start(clock=a_fixed_clock())
    session.add_exercise(an_exercise_id(), clock=a_fixed_clock())
    dto = WorkoutSessionDTO.from_workout_session(session)
    performance_dto = dto.exercise_performances[0]
    with pytest.raises(FrozenInstanceError):
        performance_dto.exercise_id = an_exercise_id()  # type: ignore[misc]
