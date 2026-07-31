"""`ApplicationResult[T]`: the single outcome shape every
`CommandHandler`/`QueryHandler` returns.

**Not the same type as `app.domain.shared_kernel.result.Result`
(`Ok`/`Err`), deliberately.** `Result` is the Domain Layer's own
"expected failure as a value" pattern for one aggregate method call: a
clean binary split, exactly one of a success value or one error value,
with no room for anything in between. `ApplicationResult` answers a
different question — "how did this whole orchestrated workflow go" —
and a workflow can finish successfully while still having something
worth telling the caller (`warnings`), or fail for more than one
reason at once (`errors` is a tuple, not a single value). Collapsing
`ApplicationResult` onto `Result` would either lose the `warnings`
channel entirely or force every domain-level `DomainError` into a
lossy string, neither of which this layer accepts. See
`docs/adr/0022-application-layer-foundation.md`.

Immutable and validated once at construction, the same discipline
every value object in this codebase already follows — `success=True`
must not carry `errors`, and `success=False` must carry at least one
error and no `value`. Use the `ok()`/`fail()` factory methods below
rather than constructing directly; they make the common cases
impossible to get backwards.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from app.application.shared.exceptions import ApplicationResultConstructionError

T = TypeVar("T")


@dataclass(frozen=True, kw_only=True)
class ApplicationResult(Generic[T]):
    """The outcome of one `CommandHandler`/`QueryHandler` invocation.

    - `success`: whether the workflow completed without a
      reportable failure.
    - `value`: the workflow's result, present only when `success` is
      `True`. `None` on failure, and legitimately `None` on a success
      that has nothing to return (e.g. a command whose only job is to
      cause a side effect).
    - `errors`: every reportable failure reason, non-empty exactly when
      `success` is `False`.
    - `warnings`: advisory messages that do not affect `success` —
      room for a handler to say "this succeeded, but here is something
      worth knowing" (e.g. a triggered `RuleResult` recommendation
      surfaced from an invoked rule engine), present on either outcome.
    """

    success: bool
    value: T | None = None
    errors: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.success and self.errors:
            raise ApplicationResultConstructionError(
                "a successful ApplicationResult must not carry errors"
            )
        if not self.success and self.value is not None:
            raise ApplicationResultConstructionError(
                "a failed ApplicationResult must not carry a value"
            )
        if not self.success and not self.errors:
            raise ApplicationResultConstructionError(
                "a failed ApplicationResult must carry at least one error"
            )

    @classmethod
    def ok(cls, value: T | None = None, *, warnings: Sequence[str] = ()) -> ApplicationResult[T]:
        """Builds a successful result. `value` defaults to `None` for
        commands whose only job is a side effect."""
        return cls(success=True, value=value, errors=(), warnings=tuple(warnings))

    @classmethod
    def fail(cls, errors: Sequence[str], *, warnings: Sequence[str] = ()) -> ApplicationResult[T]:
        """Builds a failed result. `errors` must be non-empty — a
        failure with no stated reason is exactly the inconsistency
        `__post_init__` rejects."""
        return cls(success=False, value=None, errors=tuple(errors), warnings=tuple(warnings))
