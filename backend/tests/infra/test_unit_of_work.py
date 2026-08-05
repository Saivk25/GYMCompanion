"""Tests for `SqlAlchemyUnitOfWork` — the transactional mechanics
(session lifecycle, commit/rollback, repository caching and resolution)
that `app/infra/unit_of_work.py`'s module docstring documents.

Deliberately does **not** use any of the eight real aggregate
repositories (`UserSqlRepository` and friends) for the commit/rollback
proof below: every one of those calls `app.infra.database.tenant_scope`,
which executes Postgres's `set_config(...)` — a function sqlite (used
here so these tests run with no live database, matching every other
`unit`-marked test in this suite) does not have. A minimal, test-only
aggregate/row/repository triple, built the same way every real repository
already is (subclassing `TrackingRepository`), proves
`SqlAlchemyUnitOfWork`'s own generic behavior — which does not know or
care what aggregate it is committing — without depending on
Postgres-only SQL. The eight real repositories' own construction is
proven separately, in `tests/composition/test_container.py` and
`tests/composition/test_dependency_graph.py`, without needing a working
session for it (see `SqlAlchemyUnitOfWork.get_repository`'s docstring:
constructing a repository does no I/O).
"""

from __future__ import annotations

import uuid
from collections.abc import Generator

import pytest
from sqlalchemy import String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.application.shared.exceptions import UnitOfWorkError
from app.domain.shared_kernel.aggregate_root import AggregateRoot
from app.domain.shared_kernel.identifiers import EntityId
from app.domain.shared_kernel.repository import Repository
from app.infra.repositories._tracking import TrackingRepository
from app.infra.unit_of_work import SqlAlchemyUnitOfWork


class _ScratchBase(DeclarativeBase):
    """A declarative base entirely separate from `app.infra.orm_base.
    Base` — this table must never be visible to Alembic's autogenerate
    (which inspects `Base.metadata`) or any other test's schema."""


class _ScratchRow(_ScratchBase):
    __tablename__ = "scratch_widgets"

    widget_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)


class _WidgetId(EntityId):
    pass


class _Widget(AggregateRoot[_WidgetId]):
    def __init__(self, widget_id: _WidgetId, name: str) -> None:
        super().__init__(widget_id)
        self.name = name

    def rename(self, name: str) -> None:
        self.name = name


class _WidgetRepository(Repository[_Widget, _WidgetId]):
    """Abstract contract, mirroring the shape every real `app.domain.*.
    repository` module defines — needed so `get_repository()`'s type
    parameter has something to key the registry by, the same as
    `UserRepository`/`ExerciseRepository`/etc. do for the real
    repositories."""


class _WidgetSqlRepository(_WidgetRepository, TrackingRepository[_Widget, _WidgetId, _ScratchRow]):
    def get(self, entity_id: _WidgetId) -> _Widget | None:
        row = self._session.get(_ScratchRow, str(entity_id))
        if row is None:
            return None
        widget = _Widget(entity_id, row.name)
        self._track(entity_id, widget, row)
        return widget

    def add(self, aggregate: _Widget) -> None:
        row = _ScratchRow(widget_id=str(aggregate.id))
        self._apply_to_row(aggregate, row)
        self._session.add(row)
        self._track(aggregate.id, aggregate, row)

    def remove(self, aggregate: _Widget) -> None:
        row = self._session.get(_ScratchRow, str(aggregate.id))
        if row is not None:
            self._session.delete(row)
        self._untrack(aggregate.id)

    def _apply_to_row(self, aggregate: _Widget, row: _ScratchRow) -> None:
        row.name = aggregate.name


@pytest.fixture
def session_factory() -> Generator[sessionmaker[Session], None, None]:
    engine = create_engine("sqlite://")
    _ScratchBase.metadata.create_all(engine)
    try:
        yield sessionmaker(bind=engine)
    finally:
        engine.dispose()


@pytest.fixture
def uow(session_factory: sessionmaker[Session]) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(
        session_factory,
        repository_factories={_WidgetRepository: _WidgetSqlRepository},  # type: ignore[type-abstract]
    )


@pytest.mark.unit
def test_used_outside_a_with_block_raises_unit_of_work_error(
    uow: SqlAlchemyUnitOfWork,
) -> None:
    with pytest.raises(UnitOfWorkError, match="outside a 'with' block"):
        uow.commit()


@pytest.mark.unit
def test_get_repository_for_an_unregistered_type_raises_unit_of_work_error(
    session_factory: sessionmaker[Session],
) -> None:
    empty_uow = SqlAlchemyUnitOfWork(session_factory, repository_factories={})
    with empty_uow as opened, pytest.raises(UnitOfWorkError, match="no repository registered"):
        opened.get_repository(_WidgetRepository)  # type: ignore[type-abstract]


@pytest.mark.unit
def test_get_repository_returns_the_same_instance_within_one_with_block(
    uow: SqlAlchemyUnitOfWork,
) -> None:
    with uow as opened:
        first = opened.get_repository(_WidgetRepository)  # type: ignore[type-abstract]
        second = opened.get_repository(_WidgetRepository)  # type: ignore[type-abstract]
    assert first is second
    assert isinstance(first, _WidgetSqlRepository)


@pytest.mark.unit
def test_commit_persists_a_newly_added_aggregate(uow: SqlAlchemyUnitOfWork) -> None:
    widget_id = _WidgetId(uuid.uuid4())
    with uow as opened:
        repository = opened.get_repository(_WidgetRepository)  # type: ignore[type-abstract]
        repository.add(_Widget(widget_id, "first"))
        opened.commit()

    with uow as opened:
        repository = opened.get_repository(_WidgetRepository)  # type: ignore[type-abstract]
        fetched = repository.get(widget_id)

    assert fetched is not None
    assert fetched.name == "first"


@pytest.mark.unit
def test_mutation_persists_without_a_second_add_call_after_commit(
    uow: SqlAlchemyUnitOfWork,
) -> None:
    """The exact shape every real handler already uses (`repository.get(id)`,
    mutate via a domain method, `uow.commit()`, no second `add()`) — proven
    here against `SqlAlchemyUnitOfWork` itself, generically."""
    widget_id = _WidgetId(uuid.uuid4())
    with uow as opened:
        opened.get_repository(_WidgetRepository).add(_Widget(widget_id, "original"))  # type: ignore[type-abstract]
        opened.commit()

    with uow as opened:
        repository = opened.get_repository(_WidgetRepository)  # type: ignore[type-abstract]
        fetched = repository.get(widget_id)
        assert fetched is not None
        fetched.rename("renamed")
        opened.commit()

    with uow as opened:
        refetched = opened.get_repository(_WidgetRepository).get(widget_id)  # type: ignore[type-abstract]
    assert refetched is not None
    assert refetched.name == "renamed"


@pytest.mark.unit
def test_explicit_rollback_discards_staged_changes(uow: SqlAlchemyUnitOfWork) -> None:
    widget_id = _WidgetId(uuid.uuid4())
    with uow as opened:
        opened.get_repository(_WidgetRepository).add(_Widget(widget_id, "will not survive"))  # type: ignore[type-abstract]
        opened.rollback()

    with uow as opened:
        assert opened.get_repository(_WidgetRepository).get(widget_id) is None  # type: ignore[type-abstract]


@pytest.mark.unit
def test_an_exception_inside_the_with_block_rolls_back_automatically(
    uow: SqlAlchemyUnitOfWork,
) -> None:
    """`UnitOfWork.__exit__` (`app/application/shared/unit_of_work.py`,
    inherited unchanged here) rolls back on an exception without the
    handler ever calling `rollback()` itself — this is what lets every
    real handler's `try: with self._uow as uow: ...` skip an explicit
    rollback call in its own `except` branches."""
    widget_id = _WidgetId(uuid.uuid4())

    with pytest.raises(RuntimeError), uow as opened:
        opened.get_repository(_WidgetRepository).add(_Widget(widget_id, "never committed"))  # type: ignore[type-abstract]
        raise RuntimeError("boom")

    with uow as opened:
        assert opened.get_repository(_WidgetRepository).get(widget_id) is None  # type: ignore[type-abstract]


@pytest.mark.unit
def test_session_is_closed_after_exit(uow: SqlAlchemyUnitOfWork) -> None:
    with uow as opened:
        session = opened._session
        assert session is not None
    # SQLAlchemy's Session.close() is idempotent and does not itself raise,
    # so the only observable proof from outside is that a fresh `with`
    # entry opens a *new* session rather than reusing the closed one.
    with uow as opened_again:
        assert opened_again._session is not session
