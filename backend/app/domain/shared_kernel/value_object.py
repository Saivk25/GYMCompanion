"""Base for immutable, equality-by-value domain types.

A value object has no identity — two `Weight(20, "kg")` instances are simply
equal, not "the same weight referenced twice" versus "two different
weights that happen to match". It is also never mutated after construction:
changing a unit of measure means constructing a new value object, not
setting an attribute on the old one.

Subclass as a frozen dataclass:

    @dataclass(frozen=True)
    class Weight(ValueObject):
        kilograms: float

This is not just a convention to remember. Because `ValueObject` itself is
declared `@dataclass(frozen=True)`, Python's dataclass machinery raises a
`TypeError` at class-definition time — before any instance is ever
created — if a subclass is decorated `@dataclass` without also passing
`frozen=True`. Forgetting frozen-ness is a startup crash, not a subtle bug
that surfaces later.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ValueObject:
    """Marker base for immutable value objects. See the module docstring —
    subclasses must be `@dataclass(frozen=True)` themselves."""
