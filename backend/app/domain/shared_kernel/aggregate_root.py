"""Base for aggregate roots: the entity a consistency boundary is entered
through, and the only place a domain event gets raised from.

Every mutation that should be visible outside the aggregate — as opposed to
a private, internal bookkeeping change — has its owning method call
`record_event(...)` with a `DomainEvent`. Nothing publishes these
immediately: they accumulate on the aggregate instance until a caller
(the repository/application layer, in a later sprint) calls
`pull_domain_events()` after successfully persisting the aggregate, and
only then dispatches them. This ordering — persist first, publish after —
is deliberate: an event for a change that was never actually saved (because
the transaction rolled back) must never go out.

`pull_domain_events()` *drains* the list (returns it and clears the
internal buffer) rather than just returning a copy, so the same event can
never accidentally be published twice by a caller that pulls more than
once.
"""

from typing import TypeVar

from app.domain.shared_kernel.entity import Entity
from app.domain.shared_kernel.events import DomainEvent
from app.domain.shared_kernel.identifiers import EntityId

TId = TypeVar("TId", bound=EntityId)


class AggregateRoot(Entity[TId]):
    """Base for aggregate roots. See the module docstring for the domain
    event lifecycle this adds on top of `Entity`."""

    def __init__(self, entity_id: TId) -> None:
        super().__init__(entity_id)
        self._domain_events: list[DomainEvent] = []

    def record_event(self, event: DomainEvent) -> None:
        """Queues a domain event to be published once this aggregate has
        been successfully persisted. Call from within a mutating method,
        after any invariant checks have already passed."""
        self._domain_events.append(event)

    def pull_domain_events(self) -> list[DomainEvent]:
        """Returns every event recorded since the last call, and clears the
        internal buffer — see the module docstring for why draining rather
        than copying matters."""
        events = list(self._domain_events)
        self._domain_events.clear()
        return events
