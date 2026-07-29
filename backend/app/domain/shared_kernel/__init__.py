"""The Domain Core's shared kernel: framework-independent base types every
future aggregate (Sprint 2 onward) builds on.

This package depends on nothing outside the Python standard library — see
`tests/domain/test_import_boundaries.py`, which enforces that statically
rather than trusting it to stay true by convention. `app/infra`, `app/api`,
and `app/ai` depend on `app/domain`; `app/domain` depends on nothing.

Re-exported here so a future aggregate module can write one import instead
of six:

    from app.domain.shared_kernel import AggregateRoot, EntityId, ensure

rather than reaching into each submodule individually. Each name's real
home and full documentation is in its own module — start there, not here.
"""

from app.domain.shared_kernel.aggregate_root import AggregateRoot
from app.domain.shared_kernel.clock import Clock, FixedClock, SystemClock
from app.domain.shared_kernel.entity import Entity
from app.domain.shared_kernel.errors import DomainError, DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent
from app.domain.shared_kernel.identifiers import EntityId
from app.domain.shared_kernel.repository import Repository
from app.domain.shared_kernel.result import Err, Ok, Result, unwrap_or
from app.domain.shared_kernel.service import DomainService
from app.domain.shared_kernel.validation import ensure, ensure_not_empty, ensure_positive
from app.domain.shared_kernel.value_object import ValueObject

__all__ = [
    "AggregateRoot",
    "Clock",
    "DomainError",
    "DomainEvent",
    "DomainInvariantViolationError",
    "DomainService",
    "Entity",
    "EntityId",
    "Err",
    "FixedClock",
    "Ok",
    "Repository",
    "Result",
    "SystemClock",
    "ValueObject",
    "ensure",
    "ensure_not_empty",
    "ensure_positive",
    "unwrap_or",
]
