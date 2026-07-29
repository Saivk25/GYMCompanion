"""Tests for app/domain/progress/identifiers.py.

Deliberately thin — see `tests/domain/user/test_identifiers.py`'s
docstring for why: `ProgressId`'s generic identifier behavior is the
shared kernel's own `EntityId` behavior, already fully covered by
`tests/domain/shared_kernel/test_identifiers.py`.
"""

import pytest

from app.domain.progress.identifiers import ProgressId
from app.domain.shared_kernel.identifiers import EntityId


@pytest.mark.unit
def test_progress_id_is_an_entity_id() -> None:
    assert issubclass(ProgressId, EntityId)


@pytest.mark.unit
def test_generate_returns_a_progress_id() -> None:
    assert isinstance(ProgressId.generate(), ProgressId)


@pytest.mark.unit
def test_parse_round_trips_through_str() -> None:
    original = ProgressId.generate()
    assert ProgressId.parse(str(original)) == original
