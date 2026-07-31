"""`UnitOfWork`: the transactional boundary one `Handler.handle()` call
runs inside — interface only, the same "no implementation" discipline
`repository.py` and `domain_event_dispatcher.py` both follow. A real,
Postgres-backed implementation (wrapping a SQLAlchemy `Session`) is
explicitly out of scope for this phase; it belongs to whichever future
phase first implements a use case that needs one.

Grants a handler two things, and nothing more: a way to obtain the
`Repository` it needs for whichever aggregate the workflow touches
(`get_repository()`), and a way to atomically commit or discard every
change made through those repositories during this unit of work
(`commit()`/`rollback()`). It does not know what a `User` or a
`Workout` is — `get_repository()` is generic over any
`Repository[TAggregate, TId]` subtype precisely so this interface never
needs to name a concrete aggregate repository, the same reasoning
`repository.py`'s own docstring gives for reusing the Domain Layer's
`Repository` rather than inventing per-aggregate accessors
(`uow.users`, `uow.exercises`, ...) here — that concrete wiring is a
future use-case/infrastructure concern, not a foundation concern.

`__enter__`/`__exit__` are concrete, not abstract: the context-manager
*protocol* — enter, do work, roll back automatically if something threw
— is universal coordination glue that is correct for any conceivable
`UnitOfWork` implementation, the same category of thing
`app.domain.rules.rule.Rule._pass()`/`_fail()` already are for
`Rule.evaluate()`: concrete helper behavior built on top of methods a
subclass must still supply. It is not an "implementation" in the sense
this phase excludes — no I/O, no ORM session, nothing that depends on a
real transaction ever happens here; `rollback()` and `commit()` remain
abstract, and *actually* rolling back or committing anything is left
entirely to whichever concrete subclass a future phase writes. Exiting
without an exception does **not** auto-commit — committing is always
an explicit, deliberate act a handler performs itself after every
domain-level check has passed, never an implicit side effect of leaving
a `with` block cleanly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Any, TypeVar

from app.application.shared.repository import Repository

TRepository = TypeVar("TRepository", bound=Repository[Any, Any])


class UnitOfWork(ABC):
    """Abstract transactional boundary. See the module docstring for
    what each method is responsible for, and why `__enter__`/`__exit__`
    are concrete while everything else stays abstract.
    """

    @abstractmethod
    def commit(self) -> None:
        """Atomically persists every change staged through this unit of
        work's repositories. A concrete implementation is responsible
        for making this all-or-nothing; this interface only guarantees
        the method exists and is called explicitly, never implicitly.
        """
        raise NotImplementedError  # pragma: no cover — abstract, always overridden

    @abstractmethod
    def rollback(self) -> None:
        """Discards every change staged through this unit of work's
        repositories since it began. Safe to call even if nothing was
        staged."""
        raise NotImplementedError  # pragma: no cover — abstract, always overridden

    @abstractmethod
    def get_repository(self, repository_type: type[TRepository]) -> TRepository:
        """Returns the repository instance for `repository_type`,
        scoped to this unit of work — e.g.
        `uow.get_repository(UserRepository)`. A concrete implementation
        decides how repositories are constructed and how many unit-of-
        work-scoped instances of each exist; this interface only
        guarantees the lookup is type-safe (the return type is bound to
        the requested `repository_type`, not a bare `Repository`).
        """
        raise NotImplementedError  # pragma: no cover — abstract, always overridden

    def __enter__(self) -> UnitOfWork:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Rolls back automatically if the `with` block raised — never
        suppresses the exception (this method's return is always falsy,
        matching Python's own context-manager protocol for "let it
        propagate"). Does nothing on a clean exit: committing is always
        the caller's own explicit act, never implied by leaving the
        block without an exception. See the module docstring.
        """
        if exc_type is not None:
            self.rollback()
