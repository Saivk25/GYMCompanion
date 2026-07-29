"""`Result[T, E]`: expected failures as values, not exceptions.

Domain methods that can fail for a normal, anticipated business reason
(see `errors.py` for the distinction from a bug) return a `Result` rather
than raising. This makes the failure part of the method's type signature —
a caller sees `Result[Session, DomainError]` and cannot "forget" that the
call might fail the way they could forget to catch an exception three
layers up.

`Ok` and `Err` are separate frozen types rather than one class with a
nullable value/error pair, deliberately: `some_ok_result.error` is a
`mypy` attribute error, not a runtime `None` waiting to be mishandled.
Narrow with `isinstance()` (or the `is_ok`/`is_err` properties, which mypy
does not currently narrow on, so prefer `isinstance` in new code where the
branch needs typed access to `.value`/`.error`):

    result: Result[Session, DomainError] = start_session(...)
    if isinstance(result, Err):
        return result.error
    session = result.value  # mypy knows this is Session here
"""

from dataclasses import dataclass
from typing import Generic, TypeAlias, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True)
class Ok(Generic[T]):
    """A successful result carrying `value`."""

    value: T

    @property
    def is_ok(self) -> bool:
        return True

    @property
    def is_err(self) -> bool:
        return False


@dataclass(frozen=True)
class Err(Generic[E]):
    """A failed result carrying `error`."""

    error: E

    @property
    def is_ok(self) -> bool:
        return False

    @property
    def is_err(self) -> bool:
        return True


Result: TypeAlias = Ok[T] | Err[E]


def unwrap_or(result: Result[T, E], default: T) -> T:
    """Returns the success value, or `default` if `result` is an `Err` —
    for the common case where a caller has a reasonable fallback and
    doesn't need to inspect the error."""
    if isinstance(result, Ok):
        return result.value
    return default
