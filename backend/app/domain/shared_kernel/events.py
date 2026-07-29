"""Base for domain events.

A domain event is an immutable record that something happened — past
tense, already true, never a command or a request. `occurred_at` is always
supplied by the caller (via a `Clock`, `shared_kernel/clock.py`) rather
than computed inside the event itself, so raising an event is deterministic
and testable instead of silently depending on wall-clock time.

Subclass as a frozen dataclass:

    @dataclass(frozen=True, kw_only=True)
    class UserRegistered(DomainEvent):
        user_id: UserId

`kw_only=True` on both this base and every subclass is required, not a
style choice: `event_id` below has a default value, and a plain
(positional) dataclass does not allow a subclass to add a required field
after an inherited field that has a default. Keyword-only fields have no
such ordering constraint.

This project's event system stays intentionally lightweight for now — an
in-process list an aggregate root collects (`aggregate_root.py`) and a
caller drains after a successful save, not a message broker or an event
store. See the Engineering Master Plan's over-engineering table: a broker
becomes justified by real background-job volume, not by the Domain Model
Bible naming ~50 events.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Base for immutable domain events. See the module docstring for the
    required `kw_only=True` on subclasses."""

    occurred_at: datetime
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self) -> None:
        """Validates `occurred_at`. A subclass that defines its own
        `__post_init__` (to validate its own fields) overrides this one —
        dataclasses do not chain `__post_init__` up the hierarchy
        automatically — so it must call `super().__post_init__()` itself
        to keep this check."""
        if self.occurred_at.tzinfo is None:
            raise ValueError(
                f"{type(self).__name__}.occurred_at must be timezone-aware, got a naive datetime"
            )
