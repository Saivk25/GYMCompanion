""" "Rule engine registration" / "Domain service registration" — one
registry, not two: `app.domain.shared_kernel.service.DomainService`'s own
docstring names the nine rule engines as *the* example of what a "domain
service" is in this codebase's vocabulary ("stateless business logic that
doesn't belong to any single entity... most notably the nine rule
engines"), so treating "domain service registration" and "rule engine
registration" as two separate artifacts here would register the same
eight objects twice under two different names for no benefit — a
duplication this phase's own standing instruction ("do not introduce
abstractions because they 'might be useful'") argues just as strongly
against as it does an unneeded interface.

**Every rule engine already built is a stateless, side-effect-free
singleton — safe to construct once, here, and share for the composition
root's entire lifetime**, unlike `UnitOfWork`/handlers (see
`app/infra/unit_of_work.py`'s module docstring for why those are
per-resolution, never shared). `RuleEngine.evaluate()` (`app.domain.
rules.engine`) takes its `TContext` as a call argument and mutates
nothing — `self._rules` is a `tuple` fixed at construction — so the same
`SafetyRuleEngine()` instance evaluating two different `SafetyRuleContext`
values concurrently is exactly as safe as calling a pure function twice.

**Not (yet) consumed by any existing handler.** Every mutating handler
that already invokes a rule engine (`CreateGoalHandler`,
`RecordReadinessHandler`, `LogExerciseSetHandler`, and others — see
`docs/adr/0030-composition-root.md`'s Architecture Delta Review)
constructs its own private, module-level `_rule_engine = SomeRuleEngine()`
singleton directly in its own module, a pattern already established and
accepted across every prior Application Use Cases phase and frozen, out
of scope for this phase to change. `RuleEngines` below exists as
Composition-Root-level infrastructure — a single, discoverable place a
future caller (a diagnostics endpoint, an admin tool, or a future
refactor that does thread rule engines through handler constructors)
can obtain any of the eight from, and the target `Container.validate()`
proves each of them actually constructs — not as a currently-exercised
dependency edge. This gap is disclosed, not hidden: see the Architecture
Delta Review's "Important" finding.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.exercise.rules.exercise_recommendation_rule_engine import (
    ExerciseRecommendationRuleEngine,
)
from app.domain.goal.rules.goal_alignment_rule_engine import GoalAlignmentRuleEngine
from app.domain.nutrition.rules.nutrition_rule_engine import NutritionRuleEngine
from app.domain.progress.rules.progress_evaluation_rule_engine import (
    ProgressEvaluationRuleEngine,
)
from app.domain.readiness.rules.readiness_rule_engine import ReadinessRuleEngine
from app.domain.rules.engine import RuleEngine
from app.domain.safety.rules.safety_rule_engine import SafetyRuleEngine
from app.domain.training_load.rules.training_load_rule_engine import TrainingLoadRuleEngine
from app.domain.workout.rules.progressive_overload_rule_engine import (
    ProgressiveOverloadRuleEngine,
)


@dataclass(frozen=True, slots=True)
class RuleEngines:
    """One instance of every rule engine this codebase currently has,
    each constructed with its own default rule set. See the module
    docstring for why this is one shared, immutable registry rather than
    two, and why sharing these particular instances is safe."""

    exercise_recommendation: ExerciseRecommendationRuleEngine
    goal_alignment: GoalAlignmentRuleEngine
    nutrition: NutritionRuleEngine
    progress_evaluation: ProgressEvaluationRuleEngine
    progressive_overload: ProgressiveOverloadRuleEngine
    readiness: ReadinessRuleEngine
    safety: SafetyRuleEngine
    training_load: TrainingLoadRuleEngine

    def all(self) -> tuple[RuleEngine[Any], ...]:
        """Every registered engine, for code that wants to validate or
        iterate over the whole set without naming each field — see
        `Container.validate()`."""
        return (
            self.exercise_recommendation,
            self.goal_alignment,
            self.nutrition,
            self.progress_evaluation,
            self.progressive_overload,
            self.readiness,
            self.safety,
            self.training_load,
        )


def build_rule_engines() -> RuleEngines:
    """Constructs the default `RuleEngines` registry. A function, not a
    module-level singleton, so tests can build an independent instance
    without sharing state with `Container`'s own — though since every
    engine is stateless, sharing would in fact be harmless; a function
    is simply the more conventional, easily-testable shape."""
    return RuleEngines(
        exercise_recommendation=ExerciseRecommendationRuleEngine(),
        goal_alignment=GoalAlignmentRuleEngine(),
        nutrition=NutritionRuleEngine(),
        progress_evaluation=ProgressEvaluationRuleEngine(),
        progressive_overload=ProgressiveOverloadRuleEngine(),
        readiness=ReadinessRuleEngine(),
        safety=SafetyRuleEngine(),
        training_load=TrainingLoadRuleEngine(),
    )
