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
still-session-attached row it came from, and register listeners per
`Session` (not per repository — a single unit of work may construct
several repositories sharing one session) that re-serialize every
tracked aggregate's *current* field values onto its row before SQLAlchemy
writes anything.

**Registered on both `before_commit` and `before_flush`, not
`before_flush` alone — this is a correctness fix, not a stylistic
choice.** `before_flush` only fires when SQLAlchemy's own unit of work
already considers something new, dirty, or deleted (verified empirically
against a real `Session`: `session.commit()` with nothing already marked
dirty never fires `before_flush` at all). The exact scenario this
package exists for — mutate a plain Python domain object's own fields
through its own methods, touching no SQLAlchemy-mapped attribute
directly — never marks the row dirty by itself, so relying on
`before_flush` alone silently drops every such mutation: `session.
commit()` returns successfully, but the row on disk is left unchanged.
This was not caught when `TrackingRepository` was first built (Sprint
4/5, the Persistence Layer phase) because no live Postgres was reachable
in that sandbox to actually execute a commit against — every
`@pytest.mark.integration` test that would have exercised this simply
skipped. It was caught here, in the Composition Root phase, the first
time this mechanism was actually run against a real (sqlite, for a
database-agnostic proof) database — see `tests/infra/test_unit_of_work.
py` and `docs/adr/0030-composition-root.md`'s Architecture Delta Review.
`before_commit` always fires, unconditionally, on every `session.
commit()` call (also verified empirically) — syncing there guarantees
the row is up to date *before* SQLAlchemy decides whether anything needs
flushing, which is what makes the subsequent flush (whether the one
`commit()` triggers internally, or an explicit mid-transaction `session.
flush()` a future caller might call before commit) actually see the
change. `before_flush` stays registered too, redundantly but harmlessly
(re-syncing already-current values is a no-op), so a direct `session.
flush()` call with no `commit()` around it — not used anywhere in this
codebase today, but not forbidden by `Repository`'s own contract either
— is covered as well.

This module is deliberately generic over the concrete row type: each
repository supplies its own `_apply_to_row` translation (the actual column
<-> value-object mapping for that one aggregate), and this module only owns
the identity-map bookkeeping and the two event hooks, shared once per
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

_LISTENER_REGISTERED_KEY = "_gym_sync_listeners_registered"
_TRACKED_REPOSITORIES_KEY = "_gym_tracked_repositories"


def _sync_tracked_repositories(session: Session) -> None:
    """Shared by both event hooks below. Delegates to each repository
    registered on this session's own `_sync_tracked()` — see the module
    docstring."""
    for repository in session.info.get(_TRACKED_REPOSITORIES_KEY, ()):
        repository._sync_tracked()


def _sync_before_flush(session: Session, flush_context: Any, instances: Any) -> None:
    """`before_flush` listener. See the module docstring for why this
    alone is not sufficient, and why it stays registered anyway."""
    _sync_tracked_repositories(session)


def _sync_before_commit(session: Session) -> None:
    """`before_commit` listener — the one that actually closes the gap
    `before_flush` alone leaves open. See the module docstring."""
    _sync_tracked_repositories(session)


def _ensure_listener_registered(session: Session) -> None:
    """Idempotent: a unit of work may construct one repository per
    aggregate type against the same session, and each must not register a
    second, duplicate pair of listeners on it.
    """
    if session.info.get(_LISTENER_REGISTERED_KEY):
        return
    event.listen(session, "before_flush", _sync_before_flush)
    event.listen(session, "before_commit", _sync_before_commit)
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
