"""Tests for app/domain/goal/identifiers.py.

Deliberately thin — see `tests/domain/user/test_identifiers.py`'s
docstring for why: `GoalId`'s generic identifier behavior is the shared
kernel's own `EntityId` behavior, already fully covered by
`tests/domain/shared_kernel/test_identifiers.py`.
"""

import pytest

from app.domain.goal.identifiers import GoalId
from app.domain.shared_kernel.identifiers import EntityId


@pytest.mark.unit
def test_goal_id_is_an_entity_id() -> None:
    assert issubclass(GoalId, EntityId)


@pytest.mark.unit
def test_generate_returns_a_goal_id() -> None:
    assert isinstance(GoalId.generate(), GoalId)


@pytest.mark.unit
def test_parse_round_trips_through_str() -> None:
    original = GoalId.generate()
    assert GoalId.parse(str(original)) == original
