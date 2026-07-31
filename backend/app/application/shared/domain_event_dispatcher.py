"""`DomainEventDispatcher`: framework-independent interface responsible
only for dispatching `DomainEvent`s after a successful commit.

Deliberately narrow — one method, one responsibility. It does not
decide *when* to dispatch (that is a `Handler`'s own orchestration
job: call `UnitOfWork.commit()` first, then dispatch, never the
reverse — see `app.domain.shared_kernel.aggregate_root`'s own module
docstring: "persist first, publish after... an event for a change that
was never actually saved... must never go out"), does not know *how*
events eventually reach a subscriber (an in-process call, a message
broker — this codebase currently commits to neither; see
`app.domain.shared_kernel.events`'s own module docstring on staying
"intentionally lightweight for now"), and does not implement anything
— a real dispatcher is out of scope for this phase, the same
"interface only" discipline `unit_of_work.py` and `repository.py` both
follow.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.domain.shared_kernel.events import DomainEvent


class DomainEventDispatcher(ABC):
    """Abstract contract for dispatching domain events. Every method is
    abstract — this class cannot be instantiated on its own, only
    subclassed by a real implementation.
    """

    @abstractmethod
    def dispatch(self, events: Sequence[DomainEvent]) -> None:
        """Dispatches `events`, in order, to whatever a concrete
        implementation wires them to. Expected to be called with the
        result of `AggregateRoot.pull_domain_events()` only after the
        aggregate that raised them has already been committed — see the
        module docstring. Dispatching an empty sequence is well-defined,
        not an error: it does nothing.
        """
        raise NotImplementedError  # pragma: no cover — abstract, always overridden
