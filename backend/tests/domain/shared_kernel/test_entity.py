"""Tests for app/domain/shared_kernel/entity.py."""

import pytest

from app.domain.shared_kernel.entity import Entity
from app.domain.shared_kernel.identifiers import EntityId


class _UserId(EntityId):
    pass


class _User(Entity[_UserId]):
    def __init__(self, user_id: _UserId, display_name: str) -> None:
        super().__init__(user_id)
        self.display_name = display_name


class _Workout(Entity[_UserId]):
    """Deliberately reuses _UserId as its id type, only to prove equality
    is type-scoped too (see test below) — not a realistic shape."""


@pytest.mark.unit
def test_equality_is_by_id_not_by_field_values() -> None:
    """The defining behavior of an entity, as opposed to a value object:
    two instances with the same id are the same entity even if every other
    field differs, and the same field values don't make two different-id
    instances equal."""
    shared_id = _UserId.generate()
    same_entity_different_name = _User(shared_id, "Alice")
    same_entity_different_name_2 = _User(shared_id, "Bob")
    assert same_entity_different_name == same_entity_different_name_2

    different_entity = _User(_UserId.generate(), "Alice")
    assert same_entity_different_name != different_entity


@pytest.mark.unit
def test_equality_is_scoped_by_concrete_type_too() -> None:
    """Two different entity types that happen to share an id value are
    still not equal to each other — id equality alone isn't sufficient."""
    shared_id = _UserId.generate()
    user = _User(shared_id, "Alice")
    workout = _Workout(shared_id)
    assert user != workout


@pytest.mark.unit
def test_mutating_a_field_does_not_change_identity() -> None:
    user = _User(_UserId.generate(), "Alice")
    same_reference = user
    user.display_name = "Alicia"
    assert user == same_reference


@pytest.mark.unit
def test_is_hashable_by_id() -> None:
    shared_id = _UserId.generate()
    assert hash(_User(shared_id, "Alice")) == hash(_User(shared_id, "Bob"))


@pytest.mark.unit
def test_repr_includes_the_type_name_and_id() -> None:
    user_id = _UserId.generate()
    representation = repr(_User(user_id, "Alice"))
    assert representation == f"_User(id={user_id!r})"


@pytest.mark.unit
def test_equality_against_an_unrelated_type_is_not_equal() -> None:
    user = _User(_UserId.generate(), "Alice")
    assert user != "not an entity"
