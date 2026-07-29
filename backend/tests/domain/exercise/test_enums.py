"""Tests for app/domain/exercise/enums.py."""

import pytest

from app.domain.exercise.enums import Difficulty, ExerciseStatus, MovementPattern


@pytest.mark.unit
def test_movement_pattern_has_exactly_nine_members() -> None:
    assert {member.value for member in MovementPattern} == {
        "push",
        "pull",
        "hinge",
        "squat",
        "lunge",
        "carry",
        "rotation",
        "core",
        "cardio",
    }


@pytest.mark.unit
def test_difficulty_has_exactly_three_members() -> None:
    assert {member.value for member in Difficulty} == {"beginner", "intermediate", "advanced"}


@pytest.mark.unit
def test_exercise_status_has_exactly_two_members() -> None:
    assert {member.value for member in ExerciseStatus} == {"active", "deprecated"}


@pytest.mark.unit
def test_exercise_status_is_a_str_subclass() -> None:
    """Needed so a member serializes as its plain value (JSON, a database
    column, an event payload) rather than as `ExerciseStatus.ACTIVE`."""
    assert isinstance(ExerciseStatus.ACTIVE, str)
    assert ExerciseStatus.ACTIVE.value == "active"
