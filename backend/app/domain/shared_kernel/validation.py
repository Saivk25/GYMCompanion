"""Guard-clause helpers for enforcing invariants.

These raise `DomainInvariantViolationError` (see `errors.py` for why that's the
right exception type here, as opposed to returning a `Result`): every use
of `ensure*()` is asserting something that must always be true for the
aggregate's own logic to be correct, not validating externally-supplied
input the caller might reasonably get wrong. Rejecting bad *input* with a
recoverable, business-meaningful failure is what `Result`/`DomainError` are
for; these functions are for the "this should be structurally impossible"
class of check.

Deliberately small. This is a shared-kernel utility module, not a
validation framework — add a new helper only once a second real rule
engine needs the same shape of check, not speculatively.
"""

from app.domain.shared_kernel.errors import DomainInvariantViolationError


def ensure(condition: bool, message: str) -> None:
    """Raises `DomainInvariantViolationError(message)` if `condition` is false."""
    if not condition:
        raise DomainInvariantViolationError(message)


def ensure_not_empty(value: str, field_name: str) -> str:
    """Raises unless `value` has non-whitespace content. Returns `value`
    unchanged so this composes inline: `self._name = ensure_not_empty(name, "name")`."""
    if not value or not value.strip():
        raise DomainInvariantViolationError(f"{field_name} must not be empty")
    return value


def ensure_positive(value: float, field_name: str) -> float:
    """Raises unless `value` is strictly greater than zero. Returns `value`
    unchanged, same composition pattern as `ensure_not_empty`."""
    if value <= 0:
        raise DomainInvariantViolationError(f"{field_name} must be positive, got {value}")
    return value
