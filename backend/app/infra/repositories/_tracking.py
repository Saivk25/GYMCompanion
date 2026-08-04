"""Shared machinery every SQLAlchemy-backed repository in this package uses
to bridge the abstract `Repository[TAggregate, TId]` contract (`get`/`add`/
`remove` — see `app.domain.shared_kernel.repository`) with SQLAlchemy's
flush-based unit of work.

The gap this closes: `get()` returns a plain domain aggregate, not the ORM
row itself — `app.domain` must never see a `Session` or a mapped class (see
`app/infra/orm_base.py`'s own framework-boundary rule). Every mutating
handler already built in `app/application/*/handlers` (e.g.
`UpdateProfileHandler`, `CompleteWorkoutHandler`) follows one fixed shape:
`repository.get(id)`, mutate the returned aggregate directly through its own
domain methods, then `uow.commit()` — with no second `repository.add(...)`
call to signal "this one changed, please write it back." For that shape to
actually persist anything, something has to notice the mutation and copy it
onto the row before SQLAlchemy flushes.

`TrackingRepository` closes that gap the way Chapter 2 of *Architecture
Patterns with Python* (Percival & Gregory) describes for this exact
DDD/SQLAlchemy seam: keep a private map from aggregate id to the
still-session-attached row it came from, and register one `before_flush`
listener per `Session` (not per repository — a single unit of work may
construct several repositories sharing one session) that re-serializes every
tracked aggregate's *current* field values onto its row immediately before
SQLAlchemy writes anything. `session.commit()`/`session.flush()` — called by
a future `UnitOfWork` implementation, deliberately out of scope for this
phase (see `app/application/shared/unit_of_work.py`'s own docstring: "A real,
Postgres-backed implementation ... is explicitly out of scope for this
phase") — then persists the up-to-date row exactly as if it had been mutated
directly.

This module is deliberately generic over the concrete row type: each
repository supplies its own `_apply_to_row` translation (the actual column
<-> value-object mapping for that one aggregate), and this module only owns
the identity-map bookkeeping and the one flush hook, shared once per
`Session` rather than duplicated across every repository.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.domain.shared_kernel.aggregate_root import AggregateRoot
from app.domain.shared_kernel.identifiers import EntityId

TAggregate = TypeVar("TAggregate", bound=AggregateRoot[Any])
TId = TypeVar("TId", bound=EntityId)
TRow = TypeVar("TRow")

_LISTENER_REGISTERED_KEY = "_gym_before_flush_listener_registered"
_TRACKED_REPOSITORIES_KEY = "_gym_tracked_repositories"


def _sync_before_flush(session: Session, flush_context: Any, instances: Any) -> None:
    """The one `before_flush` listener shared by every `Session` this
    package touches. Delegates to each repository registered on this
    session's own `_sync_tracked()` — see the module docstring.
    """
    for repository in session.info.get(_TRACKED_REPOSITORIES_KEY, ()):
        repository._sync_tracked()


def _ensure_listener_registered(session: Session) -> None:
    """Idempotent: a unit of work may construct one repository per
    aggregate type against the same session, and each must not register a
    second, duplicate listener on it.
    """
    if session.info.get(_LISTENER_REGISTERED_KEY):
        return
    event.listen(session, "before_flush", _sync_before_flush)
    session.info[_LISTENER_REGISTERED_KEY] = True


class TrackingRepository(Generic[TAggregate, TId, TRow]):
    """Shared base for every SQLAlchemy-backed repository in
    `app/infra/repositories/`. See the module docstring for why this exists.

    A concrete repository calls `_track()`/`_untrack()` from its own
    `get()`/`add()`/`remove()` and implements exactly one hook:

    - `_apply_to_row(aggregate, row)`: copies an aggregate's *current*
      field values onto an already-constructed or already-loaded row. Used
      both by `add()` (applied to a brand-new row, so insert and flush-time
      sync never duplicate column-mapping logic) and, automatically, by
      this base class immediately before every flush.
    """

    def __init__(self, session: Session) -> None:
        self._session = session
        self._tracked: dict[TId, tuple[TAggregate, TRow]] = {}
        session.info.setdefault(_TRACKED_REPOSITORIES_KEY, []).append(self)
        _ensure_listener_registered(session)

    def _track(self, aggregate_id: TId, aggregate: TAggregate, row: TRow) -> None:
        self._tracked[aggregate_id] = (aggregate, row)

    def _untrack(self, aggregate_id: TId) -> None:
        self._tracked.pop(aggregate_id, None)

    def _sync_tracked(self) -> None:
        for aggregate, row in self._tracked.values():
            self._apply_to_row(aggregate, row)

    def _apply_to_row(self, aggregate: TAggregate, row: TRow) -> None:
        raise NotImplementedError  # pragma: no cover — always overridden
