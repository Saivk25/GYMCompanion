"""Base for entities: identity-based equality, mutable over time.

Unlike a `ValueObject`, an `Entity` is not defined by its current field
values — a `User` is still the same `User` after changing their timezone.
Equality and hashing are therefore based on identity (`id`, plus the
concrete type) alone, deliberately overriding the field-by-field equality
Python would give a plain class or dataclass by default.

`Entity` is a plain class, not a dataclass: subclasses generally need
custom construction logic (validating invariants in `__init__`, per
`validation.py`) rather than a bag of fields assigned verbatim, which is
exactly what a dataclass is for and exactly what an entity isn't.
"""

from typing import Generic, TypeVar

from app.domain.shared_kernel.identifiers import EntityId

TId = TypeVar("TId", bound=EntityId)


class Entity(Generic[TId]):
    """Base for domain entities. Subclass and call `super().__init__(id_)`
    with the entity's own typed id (see `identifiers.py`)."""

    def __init__(self, entity_id: TId) -> None:
        self._id = entity_id

    @property
    def id(self) -> TId:
        return self._id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return type(self) is type(other) and self._id == other._id

    def __hash__(self) -> int:
        return hash((type(self), self._id))

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self._id!r})"
