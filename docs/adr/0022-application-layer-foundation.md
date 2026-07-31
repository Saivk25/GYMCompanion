# ADR 0022: Application Layer Foundation — orchestration contracts only, no use cases, re-exporting rather than duplicating Domain shapes

- Status: accepted
- Date: 2026-07-31

## Context

Sprint 4, Phase 1 asked for the Application Layer Foundation: a package
that "orchestrates the Domain Layer" by coordinating aggregates,
repository interfaces, a Unit of Work, rule engines, and domain events,
while containing "NO business rules" and remaining independent of
FastAPI, SQLAlchemy, PostgreSQL, AI, and infrastructure generally. The
task named ten files to create under `app/application/shared/` and was
explicit that use cases, concrete repositories, SQLAlchemy, FastAPI,
authentication, REST, and AI are all out of scope for this phase — only
the shared contracts those future use cases will depend on.

Four questions were specific to this phase, mirroring the task's own
ADR prompt:

1. **Why does an Application Layer need to exist at all, given the
   Domain Layer (Sprint 1–3) already enforces every invariant and every
   Rule Engine already produces deterministic verdicts?**
2. **Why does orchestration — "load this aggregate, run these rules,
   commit" — belong in a layer of its own rather than folding into a
   future FastAPI route handler directly?**
3. **How does this layer stay demonstrably independent of
   infrastructure when a Unit of Work and a Repository are, by nature,
   persistence-shaped concepts?**
4. **The Domain Layer (`app.domain.shared_kernel.repository.Repository`)
   already defines a generic repository contract. Does the Application
   Layer need its own, separate one?**

## Decision

1. **The Application Layer exists to hold the one kind of logic the
   Domain Layer cannot hold: multi-aggregate, multi-rule-engine
   workflow sequencing.** Every aggregate in `app.domain` enforces its
   own invariants in isolation (`AggregateRoot`'s own contract), and
   every Rule Engine (Sprint 3) evaluates one deterministic verdict from
   a context it is handed. Neither knows how to load a `User` and a
   `WorkoutSession` from storage, hand both to
   `ExerciseRecommendationRuleEngine`, and decide what happens to the
   result — that sequencing is a distinct responsibility with no home
   in the Domain Layer's own contracts, and giving it one prevents
   future use-case code from re-deriving this sequencing ad hoc inside
   route handlers.

2. **Orchestration belongs in its own layer, not inline in a future
   FastAPI handler, because a route handler's job is translating HTTP
   to and from application concepts — not deciding workflow order.**
   `CommandHandler`/`QueryHandler` (`app/application/shared/
   command_handler.py`, `query_handler.py`) give every future use case
   the same shape: receive a `Command` or `Query`, return an
   `ApplicationResult`. A route handler that will eventually call
   `SomeUseCase.handle(command)` never needs to know what aggregates or
   rule engines that use case touches — the same separation
   `Rule.evaluate()` gives a `RuleEngine` today, one level up the stack.
   This also makes every future use case testable without FastAPI,
   SQLAlchemy, or a running server: a `CommandHandler` subclass and a
   fake `UnitOfWork` are sufficient.

3. **`UnitOfWork` and `DomainEventDispatcher` are pure `ABC`s with zero
   I/O — the only concrete code either carries is the context-manager
   protocol on `UnitOfWork`, which is coordination glue, not
   persistence.** `UnitOfWork.__enter__` returns `self`;
   `__exit__` calls `self.rollback()` only when an exception occurred
   and never suppresses it, and never calls `commit()` on a clean exit
   — commit is always the caller's explicit act. Nothing in this
   protocol references a database, a session, a connection string, or a
   transaction isolation level; a future `SqlAlchemyUnitOfWork` will
   *implement* `commit()`/`rollback()`/`get_repository()`, but the
   ordering contract itself is framework-independent, the same
   reasoning that lets `Rule._pass()`/`_fail()` be concrete helpers atop
   `Rule.evaluate()`'s abstract contract without compromising the
   Domain Layer's independence.
   `tests/application/test_import_boundaries.py` enforces this
   statically — mirroring `tests/domain/test_import_boundaries.py` —
   allowing `app.application.*`, `app.domain.*`, and the standard
   library only; no file under `app/application/` may import
   `fastapi`, `sqlalchemy`, or any `app.infra`/`app.api` module.

4. **`app/application/shared/repository.py` re-exports
   `app.domain.shared_kernel.repository.Repository` rather than
   defining a second, structurally identical interface.** The task's
   instruction to not duplicate Domain exceptions applies with equal
   force to this second concept: `Repository[TAggregate, TId]` (Sprint
   1) already expresses "an abstract persistence contract for one
   aggregate type," and the Application Layer's own workflows need
   exactly that contract, not a variant of it. `UnitOfWork.
   get_repository(repository_type: type[TRepository]) -> TRepository`
   is deliberately generic and type-indexed rather than exposing named
   per-aggregate properties (`uow.users`, `uow.workouts`) — no concrete
   aggregate repository is wired into this phase, and a type-indexed
   lookup keeps the interface aggregate-agnostic until a future
   infrastructure phase supplies real implementations.
   `tests/application/shared/test_repository.py` asserts
   `Repository is DomainRepository` by identity, proving re-export
   rather than duplication the same way
   `tests/application/shared/test_exceptions.py` proves the exception
   hierarchy does not overlap the Domain Layer's own.

`ApplicationResult[T]` (`application_result.py`) is kept a distinct
type from the Domain Layer's `Result`/`Ok`/`Err`: `Result` expresses one
call's binary success-or-failure; `ApplicationResult` expresses a whole
workflow's outcome, including a `warnings` channel and a tuple of
`errors` neither of which a single-call `Result` needs. `Command` and
`Query` are themselves frozen dataclasses (`@dataclass(frozen=True,
kw_only=True)`), not plain marker classes, reusing the same
enforcement trick `ValueObject` already established — a subclass that
forgets `frozen=True` fails at class-definition time rather than
silently permitting mutable commands.

## Consequences

No use case exists yet — `CommandHandler`/`QueryHandler` are proven
only against fakes in this phase's own tests
(`test_command_handler.py`, `test_query_handler.py`), the same posture
`app.domain.shared_kernel.repository.Repository` had in Sprint 1 before
any concrete aggregate repository existed. A future phase that adds the
first real use case (e.g. "log a workout") will be the first real
consumer of every contract this phase defines, and is where any gap in
this foundation — a missing `ApplicationResult` shape, an
under-specified `UnitOfWork` responsibility — will first surface.

Because `DomainEventDispatcher.dispatch()` only defines *that* events
are dispatched, never *when* or *how*, every future use case must call
it explicitly after `UnitOfWork.commit()` succeeds — mirroring
`AggregateRoot`'s own "persist first, publish after" docstring. This
phase enforces nothing that would catch a future use case dispatching
events before a commit or on a rolled-back transaction; that discipline
is deferred to code review and future use-case-level tests, not encoded
in this layer's own types.

`get_repository`'s generic, type-indexed lookup means a future misuse
(requesting a repository type no concrete `UnitOfWork` implementation
registers) is only a runtime `KeyError` away rather than a static type
error — an accepted trade-off for staying aggregate-agnostic in this
phase, the same trade-off Python's own `dict`-based service lookups
generally carry, and one a future infrastructure phase's concrete
`UnitOfWork` can narrow if it proves worth doing.
