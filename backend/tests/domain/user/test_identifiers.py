"""Tests for app/domain/user/identifiers.py.

Deliberately thin: `UserId`'s generic identifier behavior (generate,
parse, frozen-ness, type-scoped equality) is the shared kernel's own
`EntityId` behavior, already fully covered by
`tests/domain/shared_kernel/test_identifiers.py`. This file only proves
`UserId` itself is usable and is a genuine `EntityId` subclass.
"""

import pytest

from app.domain.shared_kernel.identifiers import EntityId
from app.domain.user.identifiers import UserId


@pytest.mark.unit
def test_user_id_is_an_entity_id() -> None:
    assert issubclass(UserId, EntityId)


@pytest.mark.unit
def test_generate_returns_a_user_id() -> None:
    assert isinstance(UserId.generate(), UserId)


@pytest.mark.unit
def test_parse_round_trips_through_str() -> None:
    original = UserId.generate()
    assert UserId.parse(str(original)) == original
