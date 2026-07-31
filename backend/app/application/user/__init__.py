"""The User Application Use Cases — Sprint 4, Phase 2.

Coordinates the `User` aggregate (`app.domain.user`) with repository
interfaces and a `UnitOfWork` (both from `app.application.shared`),
containing no business rules of its own: every decision about what
makes a User valid, or what state transitions are legal, lives on
`User` itself. This package only sequences calls — load, mutate,
commit, dispatch — the same orchestration-not-decision boundary
`docs/adr/0022-application-layer-foundation.md` establishes for the
Application Layer generally, applied here to its first concrete
aggregate. See `docs/adr/0023-user-application-use-cases.md` for the
decisions specific to this phase.

Four subpackages, one per concern:

- `commands/`: immutable write-intent inputs (`CreateUserCommand`, ...).
- `queries/`: immutable read-intent inputs (`GetUserQuery`, ...).
- `dto/`: `UserDTO`, the read-only shape a query handler returns.
- `handlers/`: the `CommandHandler`/`QueryHandler` implementations
  that actually orchestrate.

No use case for any other aggregate (Workout, Nutrition, Progress,
Readiness, Goal, ...), no concrete repository, no SQLAlchemy, no
FastAPI, and no AI integration exists in this package — see the ADR
for what's deliberately out of scope.
"""
