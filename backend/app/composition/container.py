"""`Container`: resolves a fully-wired collaborator graph for any of this
codebase's ~43 Application Layer handlers, plus the shared singletons
(`Clock`, `DomainEventDispatcher`, the rule engine registry) every layer
above `app.domain` needs.

**The one rule this whole module exists to enforce**: nothing here is a
long-lived, shared `UnitOfWork` or handler instance. See
`app/infra/unit_of_work.py`'s module docstring for the concurrency
argument in full — the short version is that every handler already
re-enters the *same* `self._uow` object on every `handle()` call (frozen,
out of scope to change), so if `Container` cached and reused one handler
instance, two callers using it "at the same time" would race on that
instance's session. `Container.handler()` therefore constructs a brand
new handler (and therefore a brand new `SqlAlchemyUnitOfWork`) on every
call — cheap, since neither does any I/O until a handler's own `with
self._uow:` block runs. What *is* safely cached and reused across the
container's whole lifetime — `settings`, `engine`, `session_factory`,
`clock`, `dispatcher`, `rule_engines` — are all either immutable or
stateless; see each field's own type for why sharing it is safe.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, TypeVar

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.application.shared.interfaces import Handler
from app.composition.discovery import discover_handler_types
from app.composition.event_dispatcher import LoggingDomainEventDispatcher
from app.composition.rule_engines import RuleEngines, build_rule_engines
from app.core.config import Settings
from app.domain.shared_kernel.clock import Clock, SystemClock
from app.infra.unit_of_work import DEFAULT_REPOSITORY_FACTORIES, SqlAlchemyUnitOfWork

H = TypeVar("H", bound=Handler[Any, Any])


class CompositionError(Exception):
    """Raised by `Container.validate()` when some part of the dependency
    graph cannot actually be resolved — a registered repository factory
    that doesn't produce the type it's registered under, a rule engine
    that fails to construct, or a discovered handler that fails to
    resolve. Distinct from `UnitOfWorkError` (`app/application/shared/
    exceptions.py`), which is a *runtime* "no repository registered for
    this type" failure inside a request; `CompositionError` is a
    *startup-time* "the wiring itself is broken" failure — the two are
    never raised from the same call path.
    """


@dataclass(frozen=True, slots=True)
class Container:
    """Holds every shared, process-lifetime collaborator and resolves
    per-use ones (`UnitOfWork`, handlers) on demand. Construct via
    `app.composition.bootstrap.bootstrap()`, not directly — that function
    is what actually builds the `Engine`/`sessionmaker`/logging
    configuration this class is handed already-built.
    """

    settings: Settings
    engine: Engine
    session_factory: sessionmaker[Session]
    clock: Clock
    dispatcher: LoggingDomainEventDispatcher
    rule_engines: RuleEngines

    def is_database_ready(self) -> bool:
        """Opens a connection and runs a trivial query against this
        container's database, returning whether it succeeded. Never
        raises — a caller (the API Layer's `/health/ready` endpoint, see
        `app/api/routes/health.py`) that wants a plain "am I ready"
        answer without needing to know, or import, which of
        SQLAlchemy's many driver-specific exceptions to catch. This is
        the one place outside `validate()` that `Container` does real
        I/O; every other method on this class does none (see
        `app/infra/unit_of_work.py`'s module docstring for why
        constructing a `Session` never opens a connection on its own).
        """
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return False
        return True

    def unit_of_work(self) -> SqlAlchemyUnitOfWork:
        """A brand-new `UnitOfWork`, bound to this container's shared
        `session_factory`. See the module docstring for why this is
        never cached."""
        return SqlAlchemyUnitOfWork(self.session_factory)

    def handler(self, handler_type: type[H]) -> H:
        """Constructs `handler_type`, supplying `uow` (always, a fresh
        `unit_of_work()`) and `dispatcher`/`clock` (only if
        `handler_type.__init__` actually declares that parameter — see
        `docs/adr/0030-composition-root.md` for the three constructor
        shapes every handler in this codebase already follows). Works for
        any handler built so far, and for any future one that keeps to
        the same three shapes, with no per-handler registration needed.
        """
        parameters = inspect.signature(handler_type.__init__).parameters
        kwargs: dict[str, object] = {"uow": self.unit_of_work()}
        if "dispatcher" in parameters:
            kwargs["dispatcher"] = self.dispatcher
        if "clock" in parameters:
            kwargs["clock"] = self.clock
        # `handler_type(**kwargs)` with `kwargs: dict[str, object]` type-checks
        # under mypy --strict without a `# type: ignore` here — `type[H]`
        # called with `**kwargs` of an unrelated mapping type is accepted
        # dynamically, the same way `handler_type.__init__`'s own parameters
        # were only just inspected at runtime, not statically, on the line
        # above. What mypy *cannot* verify statically is that `kwargs`
        # actually matches `handler_type`'s real constructor — that
        # guarantee instead comes from `tests/composition/
        # test_dependency_graph.py` actually constructing every discovered
        # handler type and asserting the result, for all of them, not from
        # the type checker.
        return handler_type(**kwargs)

    def validate(self) -> None:
        """Actually exercises every part of the dependency graph this
        container is responsible for, raising `CompositionError` with a
        specific reason on the first failure. Does no I/O — see
        `app/infra/unit_of_work.py`'s module docstring on why constructing
        a `Session` from `session_factory` never opens a connection — so
        this is safe (and expected) to run from `bootstrap()` on every
        process start, with no live database required.
        """
        self._validate_repository_registrations()
        self._validate_rule_engines()
        self._validate_handlers()

    def _validate_repository_registrations(self) -> None:
        session = self.session_factory()
        try:
            for repository_type, factory in DEFAULT_REPOSITORY_FACTORIES.items():
                repository = factory(session)
                if not isinstance(repository, repository_type):
                    raise CompositionError(
                        f"{factory!r} is registered for {repository_type.__name__!r} "
                        f"but produced {type(repository).__name__!r}, which is not "
                        "an instance of it"
                    )
        finally:
            session.close()

    def _validate_rule_engines(self) -> None:
        for engine in self.rule_engines.all():
            if engine is None:  # pragma: no cover — dataclass fields are non-optional
                raise CompositionError("a RuleEngines field was not constructed")

    def _validate_handlers(self) -> None:
        handler_types = discover_handler_types()
        if not handler_types:
            raise CompositionError(
                "discover_handler_types() found no handlers — the discovery walk "
                "is broken, or app.application has no handlers left, either of "
                "which this validation exists to catch"
            )
        for handler_type in handler_types:
            instance = self.handler(handler_type)
            if not isinstance(instance, handler_type):
                raise CompositionError(
                    f"Container.handler({handler_type.__name__}) did not return "
                    f"an instance of {handler_type.__name__}"
                )


def build_container(settings: Settings, engine: Engine) -> Container:
    """Assembles a `Container` from already-built infrastructure
    (`engine`) and configuration (`settings`) — the shared collaborators
    (`Clock`, `DomainEventDispatcher`, rule engines) are constructed here,
    once. Split out from `bootstrap()` so container assembly (pure,
    synchronous, no logging side effects) stays independently testable
    from process-lifecycle concerns (logging configuration, `validate()`
    being called, disposal) — see `app/composition/bootstrap.py`.
    """
    session_factory: sessionmaker[Session] = sessionmaker(
        bind=engine, autoflush=False, expire_on_commit=False
    )
    return Container(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        clock=SystemClock(),
        dispatcher=LoggingDomainEventDispatcher(),
        rule_engines=build_rule_engines(),
    )


__all__ = ["CompositionError", "Container", "build_container"]
