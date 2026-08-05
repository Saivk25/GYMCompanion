"""The Composition Root: the one place in this codebase that is allowed
to know about every layer at once — `app.domain`, `app.application`,
`app.infra`, and `app.core` — and wire concrete collaborators into the
abstract seams each of those layers already defined for exactly this
purpose (`Repository`, `UnitOfWork`, `DomainEventDispatcher`, `Clock`).

Nothing under this package makes a business decision. `app/composition/
container.py` constructs objects and resolves handlers; it does not
decide what makes a `Workout` valid, what a rule engine recommends, or
how an HTTP request is shaped — those remain, respectively, `app.domain`,
`app.domain.*.rules`, and a future `app.api`'s job. See
`docs/adr/0030-composition-root.md` for the full design and the
concurrency-safety reasoning behind why nothing here is a shared,
long-lived `UnitOfWork` or handler singleton.

Deliberately sits above `app.infra` (it imports concrete SQLAlchemy-backed
classes to wire them) and is imported by nothing under `app.domain` or
`app.application` — both of those layers' own import-boundary tests
(`tests/domain/test_import_boundaries.py`, `tests/application/
test_import_boundaries.py`) already make that direction structurally
impossible, the same way they already forbid `app.infra`.
"""
