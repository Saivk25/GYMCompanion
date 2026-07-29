"""Time as an injected dependency, not a hidden global.

Any domain code that needs "now" (recording when something happened,
computing an age or a duration, deciding whether a cooldown has elapsed)
takes a `Clock` rather than calling `datetime.now()` directly. Two
consequences, both deliberate:

- Tests use `FixedClock` and get fully deterministic, flake-free assertions
  about time-dependent behavior — no `sleep()`, no "assert within a few
  milliseconds of now".
- Production code uses `SystemClock`, wired in exactly once at the
  composition root (Sprint 2's dependency wiring), not scattered through
  every module that happens to need a timestamp.

Every timestamp `Clock.now()` returns is timezone-aware UTC — a naive
`datetime` is a latent bug (ambiguous, unorderable against aware datetimes,
silently wrong across a DST boundary) and this project doesn't produce them.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone


class Clock(ABC):
    """Abstract source of the current time."""

    @abstractmethod
    def now(self) -> datetime:
        """Returns the current time as a timezone-aware UTC datetime."""
        raise NotImplementedError  # pragma: no cover — abstract, always overridden


class SystemClock(Clock):
    """The real clock. The only correct place to construct this is the
    composition root — everything else should receive a `Clock`, not build
    one, so it stays swappable for a `FixedClock` in tests."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class FixedClock(Clock):
    """A test double that returns a caller-controlled time. `advance()` lets
    a test move time forward explicitly to assert duration/cooldown/
    expiry logic without any real waiting."""

    def __init__(self, fixed: datetime) -> None:
        if fixed.tzinfo is None:
            raise ValueError("FixedClock requires a timezone-aware datetime, got a naive one")
        self._fixed = fixed

    def now(self) -> datetime:
        return self._fixed

    def advance(self, delta: timedelta) -> None:
        self._fixed = self._fixed + delta
