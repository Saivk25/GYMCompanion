"""The Nutrition Application Use Cases — Sprint 4, Phase 4.

Coordinates the `Nutrition` aggregate (`app.domain.nutrition`) with
repository interfaces and a `UnitOfWork` (both from
`app.application.shared`), containing no business rules of its own:
every decision about what makes a Nutrition entry valid lives on
`Nutrition`/its value objects themselves. This package only sequences
calls — load (or check user existence), mutate, commit, dispatch,
evaluate — the same orchestration-not-decision boundary
`docs/adr/0022-application-layer-foundation.md` establishes for the
Application Layer generally. See `docs/adr/0025-nutrition-
application-use-cases.md` for the decisions specific to this phase.

Four subpackages, one per concern, mirroring `app.application.user`/
`app.application.workout`'s own layout:

- `commands/`: immutable write-intent inputs (`RecordNutritionCommand`,
  `UpdateNutritionCommand`, `UpdateWaterCommand`,
  `UpdateNutritionNotesCommand`, `DeleteNutritionCommand`).
- `queries/`: immutable read-intent inputs (`GetNutritionQuery`,
  `ListNutritionQuery`).
- `dto/`: `NutritionDTO`, the read-only shape a query handler returns.
- `handlers/`: the `CommandHandler`/`QueryHandler` implementations
  that actually orchestrate, including `NutritionRuleEngine` —
  invoked after a successful commit, surfaced only as advisory
  `ApplicationResult.warnings`, never a reason to fail a command.

No use case for any other aggregate (Progress, Readiness, Goal, ...),
no concrete repository, no SQLAlchemy, no FastAPI, and no AI
integration exists in this package — see the ADR for what's
deliberately out of scope, including why handlers never compute
macros or calorie targets.
"""
