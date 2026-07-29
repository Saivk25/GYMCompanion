"""Tests for app/domain/goal/enums.py."""

import pytest

from app.domain.goal.enums import GoalStatus, GoalType


@pytest.mark.unit
def test_goal_type_has_exactly_six_members() -> None:
    assert {member.value for member in GoalType} == {
        "lose_fat",
        "gain_muscle",
        "maintain",
        "strength",
        "endurance",
        "general_health",
    }


@pytest.mark.unit
def test_goal_type_is_a_str_subclass() -> None:
    assert isinstance(GoalType.LOSE_FAT, str)
    assert GoalType.LOSE_FAT.value == "lose_fat"


@pytest.mark.unit
def test_goal_status_has_exactly_four_members() -> None:
    assert {member.value for member in GoalStatus} == {
        "active",
        "completed",
        "cancelled",
        "expired",
    }


@pytest.mark.unit
def test_goal_status_is_a_str_subclass() -> None:
    assert isinstance(GoalStatus.ACTIVE, str)
    assert GoalStatus.ACTIVE.value == "active"
