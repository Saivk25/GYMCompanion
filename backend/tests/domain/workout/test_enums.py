"""Tests for app/domain/workout/enums.py."""

import pytest

from app.domain.workout.enums import WorkoutStatus


@pytest.mark.unit
def test_workout_status_has_exactly_four_members() -> None:
    assert {member.value for member in WorkoutStatus} == {
        "planned",
        "in_progress",
        "completed",
        "cancelled",
    }


@pytest.mark.unit
def test_workout_status_is_a_str_subclass() -> None:
    """Needed so a member serializes as its plain value (JSON, a database
    column, an event payload) rather than as `WorkoutStatus.PLANNED`."""
    assert isinstance(WorkoutStatus.PLANNED, str)
    assert WorkoutStatus.PLANNED.value == "planned"
