"""Tests for app/domain/workout_session/enums.py."""

import pytest

from app.domain.workout_session.enums import SessionStatus


@pytest.mark.unit
def test_session_status_has_exactly_four_members() -> None:
    assert {member.value for member in SessionStatus} == {
        "planned",
        "active",
        "completed",
        "abandoned",
    }


@pytest.mark.unit
def test_session_status_is_a_str_subclass() -> None:
    """Needed so a member serializes as its plain value (JSON, a database
    column, an event payload) rather than as `SessionStatus.PLANNED`."""
    assert isinstance(SessionStatus.PLANNED, str)
    assert SessionStatus.PLANNED.value == "planned"
