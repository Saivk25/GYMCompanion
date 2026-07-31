"""Application-layer-specific exceptions.

Deliberately does not move or duplicate
`app.domain.shared_kernel.errors`'s `DomainError`/
`DomainInvariantViolationError` — those remain the Domain Layer's own
vocabulary for, respectively, expected business-rule failures (carried
as values inside a `Result`, never raised) and aggregate invariant
violations (bugs inside an aggregate's own state, always raised). See
that module's own docstring for the full distinction — it does not
change here.

The exceptions below describe a different, non-overlapping category:
failures in *this* layer's own orchestration responsibilities — an
inconsistently constructed `ApplicationResult`, a `UnitOfWork` used
outside its expected protocol, a failed domain-event dispatch. None of
these are business rules (they say nothing about whether a workout is
valid or a goal is achievable) and none are aggregate invariants (they
say nothing about an aggregate's own internal state) — they are
coordination-layer bugs, the Application Layer's own equivalent of
`DomainInvariantViolationError`, not its replacement.
"""

from __future__ import annotations


class ApplicationError(Exception):
    """Base for every exception this layer raises. Catch this, not the
    bare `Exception`, at a future composition root that wants to handle
    every Application Layer failure uniformly without also silently
    swallowing an unrelated bug.
    """


class ApplicationResultConstructionError(ApplicationError):
    """Raised when an `ApplicationResult` is constructed with an
    internally inconsistent shape — e.g. `success=True` alongside a
    non-empty `errors`, or `success=False` alongside a non-`None`
    `value`. See `application_result.py`.
    """


class UnitOfWorkError(ApplicationError):
    """Raised when a `UnitOfWork` is used outside its expected
    protocol — e.g. a concrete implementation asked for a repository
    type it has no way to provide. This phase declares no concrete
    `UnitOfWork`, so nothing in this codebase raises this yet; it exists
    for the first real implementation to use. See `unit_of_work.py`.
    """


class DomainEventDispatchError(ApplicationError):
    """Raised when dispatching one or more domain events fails. This
    phase declares no concrete `DomainEventDispatcher`, so nothing in
    this codebase raises this yet; it exists for the first real
    implementation to use. See `domain_event_dispatcher.py`.
    """
