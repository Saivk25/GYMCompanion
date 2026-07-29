"""Tests for app/domain/readiness/identifiers.py.

Deliberately thin — see `tests/domain/user/test_identifiers.py`'s
docstring for why: `ReadinessId`'s generic identifier behavior is the
shared kernel's own `EntityId` behavior, already fully covered by
`tests/domain/shared_kernel/test_identifiers.py`.
"""

import pytest

from app.domain.readiness.identifiers import ReadinessId
from app.domain.shared_kernel.identifiers import EntityId


@pytest.mark.unit
def test_readiness_id_is_an_entity_id() -> None:
    assert issubclass(ReadinessId, EntityId)


@pytest.mark.unit
def test_generate_returns_a_readiness_id() -> None:
    assert isinstance(ReadinessId.generate(), ReadinessId)


@pytest.mark.unit
def test_parse_round_trips_through_str() -> None:
    original = ReadinessId.generate()
    assert ReadinessId.parse(str(original)) == original
