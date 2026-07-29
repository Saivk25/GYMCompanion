"""The repository interface every aggregate's persistence contract
implements — defined here, in the domain, with zero knowledge of
SQLAlchemy or any other storage technology. `app/infra/` provides the real
implementation for each aggregate; `app/domain/` (and anything that tests
against it) can depend only on this abstract contract.

This is what makes "Domain depends on nothing; Infrastructure depends on
Domain" true in practice rather than just asserted: a domain-layer piece of
business logic that needs to look up or save an aggregate takes a
`Repository[TheAggregate, TheAggregateId]` — an interface it owns — and is
handed a concrete SQLAlchemy-backed implementation at the composition root
(Sprint 2), never imports `app.infra` itself.

Deliberately synchronous, matching `app/infra/database.py`'s synchronous
`Session` (Step 9) rather than introducing `AsyncSession` through this
interface — the infra layer this will be implemented against is already
sync; an async repository interface today would be a mismatch invented
ahead of any actual async I/O need.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from app.domain.shared_kernel.aggregate_root import AggregateRoot
from app.domain.shared_kernel.identifiers import EntityId

# bound=AggregateRoot[Any], not bare AggregateRoot: AggregateRoot is itself
# generic over its id type, so mypy --strict requires a type argument here
# too. Any is correct, not a shortcut, because TAggregate must accept an
# AggregateRoot parameterized with *any* EntityId subclass, not one
# specific one.
TAggregate = TypeVar("TAggregate", bound=AggregateRoot[Any])
TId = TypeVar("TId", bound=EntityId)


class Repository(ABC, Generic[TAggregate, TId]):
    """Abstract persistence contract for one aggregate type. Every method
    is abstract — this class cannot be instantiated on its own (see
    `tests/domain/shared_kernel/test_repository.py`), only subclassed by a
    real implementation in `app/infra/`."""

    @abstractmethod
    def get(self, entity_id: TId) -> TAggregate | None:
        """Returns the aggregate with this id, or `None` if it doesn't
        exist. Not finding one is an expected outcome, not an error — it is
        not raised as an exception and not wrapped in a `Result`."""
        raise NotImplementedError  # pragma: no cover — abstract, always overridden

    @abstractmethod
    def add(self, aggregate: TAggregate) -> None:
        """Stages a new aggregate for persistence."""
        raise NotImplementedError  # pragma: no cover — abstract, always overridden

    @abstractmethod
    def remove(self, aggregate: TAggregate) -> None:
        """Stages an existing aggregate for deletion."""
        raise NotImplementedError  # pragma: no cover — abstract, always overridden
