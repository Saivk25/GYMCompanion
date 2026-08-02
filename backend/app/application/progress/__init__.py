"""The Progress Application Use Cases — Sprint 4, Phase 5.

Coordinates the `Progress` aggregate (`app.domain.progress`) with
repository interfaces and a `UnitOfWork` (both from
`app.application.shared`), containing no business rules of its own:
every decision about what makes a Progress record valid lives on
`Progress`/its value objects themselves, and no handler in this package
computes a trend, streak, or personal record — that remains Progress
Intelligence's job (`progress.py`'s own module docstring), not yet
built. See `docs/adr/0026-progress-application-use-cases.md` for the
decisions specific to this phase, including why
`ProgressEvaluationRuleEngine` recommendations are advisory, why
handlers never calculate trends, and why analytics remain outside the
Application Layer.

Four subpackages, one per concern, mirroring `app.application.nutrition`/
`app.application.workout`'s own layout:

- `commands/`: immutable write-intent inputs (`RecordProgressCommand`,
  `UpdateBodyCompositionCommand`, `UpdateMeasurementsCommand`,
  `UpdateNotesCommand`, `DeleteProgressCommand`).
- `queries/`: immutable read-intent inputs (`GetProgressQuery`,
  `ListProgressQuery`).
- `dto/`: `ProgressDTO`, the read-only shape a query handler returns.
- `handlers/`: the `CommandHandler`/`QueryHandler` implementations that
  actually orchestrate, including `ProgressEvaluationRuleEngine` —
  invoked after a successful commit from the user's full check-in
  history, surfaced only as advisory `ApplicationResult.warnings`,
  never a reason to fail a command.

No use case for Readiness or Goal, no concrete repository, no
SQLAlchemy, no FastAPI, and no AI integration exists in this package —
see the ADR for what's deliberately out of scope.
"""
