"""The Readiness Application Use Cases — Sprint 4, Phase 6.

Coordinates the `Readiness` aggregate (`app.domain.readiness`) with
repository interfaces and a `UnitOfWork` (both from
`app.application.shared`), containing no business rules of its own:
every decision about what makes a Readiness check-in valid lives on
`Readiness`/its value objects themselves. This package only sequences
calls — load (or check user existence), mutate, commit, dispatch,
evaluate — the same orchestration-not-decision boundary
`docs/adr/0022-application-layer-foundation.md` establishes for the
Application Layer generally. See `docs/adr/0027-readiness-
application-use-cases.md` for the decisions specific to this phase.

Four subpackages, one per concern, mirroring `app.application.nutrition`/
`app.application.progress`'s own layout:

- `commands/`: immutable write-intent inputs (`RecordReadinessCommand`,
  `UpdateSleepCommand`, `UpdateRecoveryMetricsCommand`,
  `UpdateNotesCommand`, `DeleteReadinessCommand`).
- `queries/`: immutable read-intent inputs (`GetReadinessQuery`,
  `ListReadinessQuery`).
- `dto/`: `ReadinessDTO`, the read-only shape a query handler returns.
- `handlers/`: the `CommandHandler`/`QueryHandler` implementations
  that actually orchestrate, including `ReadinessRuleEngine` —
  invoked after a successful commit, surfaced only as advisory
  `ApplicationResult.warnings`, never a reason to fail a command.

No use case for Goal, no concrete repository, no SQLAlchemy, no
FastAPI, and no AI integration exists in this package — see the ADR
for what's deliberately out of scope.
"""
