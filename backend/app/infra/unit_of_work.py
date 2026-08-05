"""`SqlAlchemyUnitOfWork`: the concrete, Postgres-backed `UnitOfWork`
`app/application/shared/unit_of_work.py`'s own docstring named as "out of
scope for this phase" — that phase has now arrived (Composition Root).

**Not a singleton, never shared across concurrent callers.** Every
mutating and read-side handler this codebase already has (frozen, out of
scope to change — see `docs/adr/0030-composition-root.md`) stores its
`uow` collaborator once, in `__init__`, and re-enters the *same* object
on every `handle()` call via `with self._uow as uow:`. If one
`SqlAlchemyUnitOfWork` instance were shared by a handler that itself was
reused across concurrent requests, two callers entering it at once would
race on `self._session` — one request's commit could run against another
request's session. The fix is not inside this class; it is a rule
`app/composition/container.py` enforces at the call site: `Container.
handler()` constructs a brand-new `SqlAlchemyUnitOfWork` (and therefore a
brand-new handler) on every resolution, never caches one. Constructing
this class does no I/O — only `__enter__` opens a session — so that rule
costs nothing.

**Session lifecycle**: `__enter__` opens a fresh `Session` from the
injected `session_factory` (a `sqlalchemy.orm.sessionmaker`, itself
thread-safe — only the `Session` *instances* it produces are not) and
resets the per-use repository cache; `__exit__` always closes that
session (via a `finally`, even if `UnitOfWork.__exit__`'s own inherited
rollback-on-exception logic runs first) and clears the cache, so a
`SqlAlchemyUnitOfWork` instance is fully reusable across multiple
sequential `with` blocks if a caller ever chose to reuse one — it just
must never be entered by two callers *at the same time*, the same
single-threaded-per-instance assumption every `Session` itself already
carries.

**Repository resolution**: `get_repository(SomeRepository)` looks
`SomeRepository` up in `repository_factories` (defaults to
`DEFAULT_REPOSITORY_FACTORIES` below — the Persistence Layer's eight
concrete classes, keyed by the abstract `Repository` type each one
implements) and constructs it against this unit of work's current
session, caching the instance so a handler that calls `get_repository`
twice for the same type within one `with` block (none currently do, but
the contract allows it) gets the same object back rather than two
independent `TrackingRepository` identity maps. Raises the existing,
previously-unused `UnitOfWorkError` ("a `UnitOfWork`... asked for a
repository type it has no way to provide" — see
`app/application/shared/exceptions.py`'s own docstring, written before
this class existed to describe exactly this failure) for an
unregistered type, and if `get_repository`/`commit`/`rollback` is called
outside an active `with` block at all.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import TracebackType
from typing import Any, TypeVar, cast

from sqlalchemy.orm import Session, sessionmaker

from app.application.shared.exceptions import UnitOfWorkError
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.exercise.repository import ExerciseRepository
from app.domain.goal.repository import GoalRepository
from app.domain.nutrition.repository import NutritionRepository
from app.domain.progress.repository import ProgressRepository
from app.domain.readiness.repository import ReadinessRepository
from app.domain.shared_kernel.repository import Repository
from app.domain.user.repository import UserRepository
from app.domain.workout.repository import WorkoutRepository
from app.domain.workout_session.repository import WorkoutSessionRepository
from app.infra.repositories.exercise_repository import ExerciseSqlRepository
from app.infra.repositories.goal_repository import GoalSqlRepository
from app.infra.repositories.nutrition_repository import NutritionSqlRepository
from app.infra.repositories.progress_repository import ProgressSqlRepository
from app.infra.repositories.readiness_repository import ReadinessSqlRepository
from app.infra.repositories.user_repository import UserSqlRepository
from app.infra.repositories.workout_repository import WorkoutSqlRepository
from app.infra.repositories.workout_session_repository import WorkoutSessionSqlRepository

TRepository = TypeVar("TRepository", bound=Repository[Any, Any])

RepositoryFactory = Callable[[Session], Repository[Any, Any]]

# "Repository registration" (Composition Root objective): the one place
# that maps each aggregate's abstract `Repository` interface — the type
# every handler already asks `get_repository()` for — to the concrete
# SQLAlchemy-backed class that satisfies it. Every value here is simply
# the concrete class itself: `UserSqlRepository(session)` already matches
# `RepositoryFactory`'s shape (one positional `Session`, returns a
# `Repository`), so no separate lambda/factory function is needed per
# aggregate — the class *is* the factory.
#
# Every line below carries `# type: ignore[type-abstract]`: mypy checks a
# dict literal's entries against `Mapping[type[Repository[Any, Any]],
# RepositoryFactory]` key-by-key, and each key (`UserRepository`,
# `ExerciseRepository`, ...) is itself an abstract class — exactly the
# same documented, narrow gap every `uow.get_repository(SomeRepository)`
# call site elsewhere in this codebase already carries the identical
# comment for: a `type[AbstractBase]` used only as a lookup key/type
# parameter, never instantiated directly.
DEFAULT_REPOSITORY_FACTORIES: Mapping[type[Repository[Any, Any]], RepositoryFactory] = {
    UserRepository: UserSqlRepository,  # type: ignore[type-abstract]
    ExerciseRepository: ExerciseSqlRepository,  # type: ignore[type-abstract]
    WorkoutRepository: WorkoutSqlRepository,  # type: ignore[type-abstract]
    WorkoutSessionRepository: WorkoutSessionSqlRepository,  # type: ignore[type-abstract]
    ProgressRepository: ProgressSqlRepository,  # type: ignore[type-abstract]
    NutritionRepository: NutritionSqlRepository,  # type: ignore[type-abstract]
    ReadinessRepository: ReadinessSqlRepository,  # type: ignore[type-abstract]
    GoalRepository: GoalSqlRepository,  # type: ignore[type-abstract]
}


class SqlAlchemyUnitOfWork(UnitOfWork):
    """Postgres-backed `UnitOfWork`. See the module docstring for session
    lifecycle, repository resolution, and — most importantly — why this
    class must never be shared across concurrent callers."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        *,
        repository_factories: Mapping[type[Repository[Any, Any]], RepositoryFactory] | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._repository_factories = repository_factories or DEFAULT_REPOSITORY_FACTORIES
        self._session: Session | None = None
        self._repositories: dict[type[Repository[Any, Any]], Repository[Any, Any]] = {}

    def __enter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._session_factory()
        self._repositories = {}
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            super().__exit__(exc_type, exc_value, traceback)
        finally:
            session, self._session = self._session, None
            self._repositories = {}
            if session is not None:
                session.close()

    def commit(self) -> None:
        self._require_session().commit()

    def rollback(self) -> None:
        self._require_session().rollback()

    def get_repository(self, repository_type: type[TRepository]) -> TRepository:
        if repository_type not in self._repositories:
            factory = self._repository_factories.get(repository_type)
            if factory is None:
                raise UnitOfWorkError(
                    f"no repository registered for {repository_type.__name__!r} — "
                    "see app.infra.unit_of_work.DEFAULT_REPOSITORY_FACTORIES"
                )
            self._repositories[repository_type] = factory(self._require_session())
        # Every value stored under `repository_type` was constructed by
        # that same key's own factory, so it is always exactly the type
        # the caller asked for — `get_repository`'s abstract contract
        # (`app/application/shared/unit_of_work.py`) already guarantees
        # this at the type level for any well-formed factory mapping;
        # this cast makes that guarantee explicit for mypy, which cannot
        # otherwise narrow a `dict[type[Repository[Any, Any]], ...]`
        # lookup to the caller's specific `TRepository`.
        return cast(TRepository, self._repositories[repository_type])

    def _require_session(self) -> Session:
        if self._session is None:
            raise UnitOfWorkError(
                "SqlAlchemyUnitOfWork used outside a 'with' block — no session is open"
            )
        return self._session
