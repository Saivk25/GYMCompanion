"""`ExerciseRecommendationRuleContext`: the `RuleContext`
(`app.domain.rules`) subtype every exercise recommendation rule in this
package evaluates against.

**One candidate exercise per evaluation.** Unlike every prior engine,
which evaluates "the user's current state" once, this engine answers a
per-candidate question: "should *this* `Exercise` be recommended right
now?" The application layer is expected to build one context per
candidate `Exercise` and call `ExerciseRecommendationRuleEngine.
evaluate()` once per candidate — looping over candidates, and over
users, is that future application layer's concern, not this package's.
`exercise: ExerciseContext` is therefore the one required field; every
other field is optional supporting evidence.

**Composes other engines' *outputs*, not their inputs.** This is the
central discipline `docs/adr/0021-exercise-recommendation-composes-
rule-outputs.md` documents in full: `safety_result` and
`readiness_result` are the already-computed `RuleResult` a caller got
back from `SafetyRuleEngine.evaluate()` / a Readiness rule engine's
`evaluate()` — this package reads their `passed`/`severity` verdicts
as-is and never re-derives whether it is safe to train or whether
today's readiness is good, the same "consume, don't duplicate"
discipline every prior engine's rules already apply to *fields*, taken
one level up to apply to *whole prior verdicts*. `progressive_overload:
ProgressiveOverloadRuleContext | None` is the one exception: it is
referenced as a whole raw snapshot (the same shape ADR 0016/0018
established), not as a `RuleResult`, because `ProgressionStageRule`
below asks a question Progressive Overload's own rules never ask
("how much training history exists," a session *count*) rather than
re-asking a question Progressive Overload's rules already answer
("is training trending up, plateaued, or declining").

**Two small, new supplied value objects, reused rather than
redefined where a type already exists.** `declared_restrictions:
tuple[DeclaredRestriction, ...]` reuses
`app.domain.safety.rules.context.DeclaredRestriction` directly — the
exact type Safety's own `ContraindicationRule` docstring, and
`docs/adr/0018-safety-rule-engine-composition-and-authority.md`'s
Consequences section, already named as this future engine's job:
"a real, exercise-selection-level `Exercise.contraindication_tags`
gate... remains future scope for an Exercise Recommendation/
Substitution engine." `available_equipment:
frozenset[EquipmentRequirement] | None` reuses `Exercise`'s own
`EquipmentRequirement` value object — no `EnvironmentContext`
aggregate exists yet to source "what equipment is available" from (the
Bible's Section 4.3), so, like `TrainingLoadSummary` before it, this
data is trusted as supplied by the caller. `recent_movement_patterns:
tuple[MovementPattern, ...]` is the one genuinely new concept: a flat,
unordered tally of movement patterns from recent training, supplied by
the caller because no existing context tracks per-pattern volume or
frequency — `WorkoutSessionSummary` (`app.domain.workout.rules.context`)
is deliberately whole-session granularity only (ADR 0017). Counting
*occurrences*, not volume, is this rule's own stated simplification of
the Bible's literal "push volume exceeds pull volume" (Table 48) — see
`movement_balance_rule.py`'s own docstring.

No wall-clock reads anywhere in this package, the same discipline
every prior context establishes: nothing here asks "how does this
compare to today."
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.exercise.context import ExerciseContext
from app.domain.exercise.enums import MovementPattern
from app.domain.exercise.value_objects import EquipmentRequirement
from app.domain.goal.context import GoalContext
from app.domain.rules.context import RuleContext
from app.domain.rules.result import RuleResult
from app.domain.safety.rules.context import DeclaredRestriction
from app.domain.workout.rules.context import ProgressiveOverloadRuleContext


@dataclass(frozen=True, kw_only=True)
class ExerciseRecommendationRuleContext(RuleContext):
    """One evaluation's worth of exercise recommendation data, scoped to
    one candidate `Exercise`. See this module's own docstring for what
    each field means and why it takes the shape it does.
    """

    exercise: ExerciseContext
    goal: GoalContext | None = None
    safety_result: RuleResult | None = None
    readiness_result: RuleResult | None = None
    progressive_overload: ProgressiveOverloadRuleContext | None = None
    declared_restrictions: tuple[DeclaredRestriction, ...] = field(default_factory=tuple)
    available_equipment: frozenset[EquipmentRequirement] | None = None
    recent_movement_patterns: tuple[MovementPattern, ...] = field(default_factory=tuple)
