"""`LoggingDomainEventDispatcher`: the first concrete
`DomainEventDispatcher` (`app/application/shared/domain_event_dispatcher.
py`) this codebase has.

**Deliberately the simplest implementation that satisfies the interface,
not a subscriber/pub-sub registry.** `app.domain.shared_kernel.events`'s
own module docstring is explicit that this project's event system "stays
intentionally lightweight for now — an in-process list an aggregate root
collects and a caller drains after a successful save, not a message
broker or an event store." Nothing in this codebase has a subscriber yet
— no read model, no notification service, no outbox — so a dispatcher
that maintains a registry of per-event-type callbacks would be exactly
the speculative abstraction the Composition Root's own standing
instruction forbids ("do not introduce abstractions because they 'might
be useful'"). This dispatcher instead logs each event, once, at INFO,
through the same root-logger configuration `logging_config.py` installs
— dispatching is observable (see `test_event_dispatcher.py`'s
`caplog`-based proof) without inventing anywhere for a real subscriber to
register until one is actually needed.

Raises the existing, previously-unused `DomainEventDispatchError` (see
`app/application/shared/exceptions.py`'s own docstring — written before
this class existed, to describe exactly this failure) if formatting or
logging an event itself raises, which keeps that exception meaningful
rather than permanently dead code. In practice this is very unlikely —
`logging` calls are not supposed to raise for a well-formed record — but
`dispatch()` is always called after `UnitOfWork.commit()` has already
succeeded (see `DomainEventDispatcher`'s own docstring: "persist first,
publish after"), so surfacing a dispatch failure as a *distinct*
exception type, rather than letting a bare `AttributeError` or similar
propagate, is what lets a future caller tell "the save succeeded but
publishing what happened did not" apart from every other failure mode.
"""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Sequence

from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.exceptions import DomainEventDispatchError
from app.domain.shared_kernel.events import DomainEvent

logger = logging.getLogger(__name__)


class LoggingDomainEventDispatcher(DomainEventDispatcher):
    """Logs every dispatched `DomainEvent` at INFO. See the module
    docstring for why this, and not a subscriber registry, is the right
    amount of implementation for this phase."""

    def dispatch(self, events: Sequence[DomainEvent]) -> None:
        for event in events:
            try:
                logger.info(
                    "domain event dispatched: %s %s",
                    type(event).__name__,
                    dataclasses.asdict(event),
                )
            except Exception as exc:  # pragma: no cover — logging a well-formed
                # frozen dataclass does not raise in practice; guarded anyway so
                # a dispatch failure is never confused with an unrelated bug.
                raise DomainEventDispatchError(
                    f"failed to dispatch {type(event).__name__}: {exc}"
                ) from exc
