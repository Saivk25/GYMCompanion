"""The Workout Application Use Cases — Sprint 4, Phase 3.

Coordinates the `Workout` and `WorkoutSession` aggregates
(`app.domain.workout`, `app.domain.workout_session`) with repository
interfaces and a `UnitOfWork` (both from `app.application.shared`),
containing no business rules of its own: every decision about what
makes a Workout or WorkoutSession valid, or what state transitions are
legal, lives on those aggregates themselves. This package only
sequences calls — load, mutate, commit, dispatch — the same
orchestration-not-decision boundary `docs/adr/0022-application-layer-
foundation.md` establishes for the Application Layer generally,
extended here to a phase whose handlers coordinate *two* aggregates in
one transaction. See `docs/adr/0024-workout-application-use-cases.md`
for the decisions specific to this phase.

Four subpackages, one per concern, mirroring
`app.application.user`'s own layout:

- `commands/`: immutable write-intent inputs (`CreateWorkoutCommand`,
  `StartWorkoutSessionCommand`, ...).
- `queries/`: immutable read-intent inputs (`GetWorkoutQuery`, ...).
- `dto/`: `WorkoutDTO`/`WorkoutSessionDTO`, the read-only shapes a
  query handler returns.
- `handlers/`: the `CommandHandler`/`QueryHandler` implementations
  that actually orchestrate, including two deterministic Rule Engines
  (`ExerciseRecommendationRuleEngine`, `ProgressiveOverloadRuleEngine`,
  `TrainingLoadRuleEngine`) invoked for advisory `warnings` only —
  never to block a workflow.

No use case for any other aggregate (Nutrition, Progress, Readiness,
Goal, ...), no concrete repository, no SQLAlchemy, no FastAPI, and no
AI integration exists in this package — see the ADR for what's
deliberately out of scope.
"""
