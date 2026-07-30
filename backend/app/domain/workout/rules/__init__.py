"""The Progressive Overload Rule Engine: Sprint 3 Phase 5's fourth
concrete deterministic rule engine, built on the Phase 1 Rule Engine
foundation (`app.domain.rules`) and the WorkoutSession aggregate
(`app.domain.workout_session`), following the same "configuration-only
subclass" and "independent rules, missing data passes" patterns
`app.domain.readiness.rules`, `app.domain.nutrition.rules`, and
`app.domain.goal.rules` already establish.

This engine evaluates workout progression over time — from an ordered
history of `WorkoutSessionSummary` values, each pre-computed once from an
immutable `WorkoutSessionContext` snapshot (`context.py`) — and produces
deterministic `Recommendation`s only. No AI, no workout generation, no
exercise substitution, no fatigue scoring, no scheduling.

Five independent rules (`VolumeRule`, `IntensityRule`, `FrequencyRule`,
`ProgressionRule`, `DeloadRule`), composed by
`ProgressiveOverloadRuleEngine` (itself a thin, behavior-preserving
configuration of the shared `RuleEngine[ProgressiveOverloadRuleContext]`).
See `docs/adr/0017-progressive-overload-session-level-trends.md` for the
architectural decisions specific to evaluating historical trends while
keeping the engine deterministic and free of repository/service access —
building on `docs/adr/0014-readiness-rule-composition.md`'s still-governing
independent-rule composition strategy.

Lives under `app.domain.workout.rules`, not `app.domain.workout_session.rules`
— the Domain Model & Decision Engine Bible's Section 10.1 "Workout Rules"
("Governs plan generation, volume, and substitution") names the volume/
progression concern this engine implements as part of the Workout bounded
context, and this phase's own task specifies this exact path. The package
depends one-directionally on `app.domain.workout_session` (for
`WorkoutSessionContext` and its own value objects) to build its context;
`app.domain.workout_session` has no reverse dependency on this package —
enforced by the same statically-checked rule as the rest of `app/domain`
(`tests/domain/test_import_boundaries.py`).

No `repository.py` in this package, the same reasoning
`app.domain.rules.__init__`'s own docstring documents: this engine
consumes context objects, never loads its own data.
"""

from app.domain.workout.rules.context import ProgressiveOverloadRuleContext, WorkoutSessionSummary
from app.domain.workout.rules.deload_rule import DeloadRule
from app.domain.workout.rules.frequency_rule import FrequencyRule
from app.domain.workout.rules.intensity_rule import IntensityRule
from app.domain.workout.rules.progression_rule import ProgressionRule
from app.domain.workout.rules.progressive_overload_rule_engine import ProgressiveOverloadRuleEngine
from app.domain.workout.rules.volume_rule import VolumeRule

__all__ = [
    "DeloadRule",
    "FrequencyRule",
    "IntensityRule",
    "ProgressionRule",
    "ProgressiveOverloadRuleContext",
    "ProgressiveOverloadRuleEngine",
    "VolumeRule",
    "WorkoutSessionSummary",
]
