"""Two distinct kinds of "wrong", handled two different ways.

1. **Expected business-rule failures** — "this workout can't be logged
   because the session was already closed", "email already registered".
   These are normal, anticipated outcomes of calling domain code with
   business-invalid input, not bugs. They are represented as *values*:
   construct a `DomainError` and return it inside `Result.err(...)`
   (`shared_kernel/result.py`), never raise it. A caller is expected to
   handle both branches of a `Result`, the same way it's expected to handle
   both branches of an `if`.

2. **Invariant violations** — a bug, not a business outcome. An aggregate's
   internal state should never be able to reach an invalid configuration
   through its own public methods; if one manages to anyway, that's a
   programming error, not a business rule failing. `DomainInvariantViolationError`
   is raised (see `validation.py`'s `ensure()`), not returned, because there
   is no meaningful way for a caller to "handle" a broken invariant other
   than letting it propagate and failing loudly.

Rule of thumb: if the Product Bible or Domain Model Bible describes the
failure as something that can legitimately happen, it's a `DomainError`. If
it would mean this aggregate's own code has a bug, it's a
`DomainInvariantViolationError`.
"""

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class DomainError:
    """A business-meaningful failure, carried as a value inside
    `Result.err(...)`. Subclass per failure kind as real rules are
    implemented (e.g. `class SessionAlreadyClosed(DomainError)`), rather
    than stringly-typing every failure through this base class directly.
    """

    code: str
    message: str


class DomainInvariantViolationError(Exception):
    """Raised when an aggregate's own internal state contradicts a rule it
    is supposed to be impossible to break — a bug inside the aggregate, not
    a business-rule rejection of the caller's input. See the module
    docstring for the distinction from `DomainError`."""
