"""Typed identifiers.

A raw `uuid.UUID` (or worse, a `str`) passed around lets a `WorkoutId` be
handed to a function expecting a `UserId` with no error until, at best, a
confusing runtime failure — "primitive obsession", one of the most common
sources of real bugs in code with many similarly-shaped aggregates. `EntityId`
exists so every aggregate defines its own distinct, non-interchangeable ID
type by subclassing it, at zero runtime cost and for free static-typing
protection from mypy.

Usage (an aggregate's own module, not this one):

    class UserId(EntityId):
        pass

    user_id = UserId.generate()
    same_id = UserId.parse(str(user_id))
    assert user_id == same_id

`UserId` and, say, `WorkoutId` are different types to mypy even though both
are structurally "an EntityId wrapping a UUID" — passing one where the other
is expected is a type error, not just a convention someone has to remember.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TypeVar

TId = TypeVar("TId", bound="EntityId")


@dataclass(frozen=True, slots=True)
class EntityId:
    """Base type for a strongly-typed aggregate/entity identifier.

    Subclass per aggregate (`class UserId(EntityId): pass`) rather than
    using this class directly — see the module docstring for why.
    """

    value: uuid.UUID

    @classmethod
    def generate(cls: type[TId]) -> TId:
        """Creates a new, random identifier of the calling subclass's type."""
        return cls(uuid.uuid4())

    @classmethod
    def parse(cls: type[TId], raw: str) -> TId:
        """Parses a string form (e.g. from a URL path or a database column)
        into the calling subclass's type. Raises `ValueError` — not a bare
        `uuid.UUID`'s cryptic message — on malformed input."""
        try:
            return cls(uuid.UUID(raw))
        except (ValueError, AttributeError, TypeError) as exc:
            raise ValueError(f"{cls.__name__}: not a valid identifier: {raw!r}") from exc

    def __str__(self) -> str:
        return str(self.value)
