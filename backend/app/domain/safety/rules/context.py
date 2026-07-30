"""`SafetyRuleContext`: the `RuleContext` (`app.domain.rules`) subtype
every safety rule in this package evaluates against.

Composed from other engines' own context types rather than flattening
their fields — `readiness: ReadinessContext | None` and
`recent_training: ProgressiveOverloadRuleContext | None` are referenced
whole, the same "reference whole snapshots" shape
`docs/adr/0016-goal-alignment-combines-whole-snapshots.md` established
for `GoalAlignmentRuleContext`, because `ReadinessSafetyRule`/
`SorenessRule` and `WorkloadRule` each need most of what their source
context already carries, not a small fixed subset.

No `GoalContext` field, even though this phase's own task names it as
something the context "may include... when needed": none of this
package's five named rules (`ReadinessSafetyRule`, `SorenessRule`,
`WorkloadRule`, `ContraindicationRule`, `InjuryRule`) need goal data to
do their job — a goal's target date or priority has no bearing on
whether it's currently safe to train. Adding an unused field would
repeat the mistake `NutritionRuleContext`'s own docstring already warns
against (no `sugar` field there, because no rule reads it). A future
rule that genuinely needs goal-aware safety context (e.g. an aggressive
deficit goal combined with a red-flag readiness signal) can add the
field when that rule is actually written.

`declared_restrictions` and `active_injuries` are new, small value
objects (`DeclaredRestriction`, `ActiveInjury`, both below) that exist
nowhere else in this codebase — no `SafetyFlag` aggregate has been built
yet (the Domain Model & Decision Engine Bible names one, Section 5's
catalog, "a structured injury/symptom flag on the Profile", but the
`User`/`UserProfile` docstring already documents that this codebase
omits it rather than adding a placeholder). This phase's own task says
`ContraindicationRule`/`InjuryRule` evaluate restrictions/injuries
"supplied in the context" — exactly what these two new value objects
are for: a caller (a future application layer, not built here) hands
over whatever it already knows, and this package neither invents a
persistence shape for that data nor queries anywhere to find it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.readiness.context import ReadinessContext
from app.domain.rules.context import RuleContext
from app.domain.shared_kernel.validation import ensure_not_empty
from app.domain.shared_kernel.value_object import ValueObject
from app.domain.workout.rules.context import ProgressiveOverloadRuleContext


@dataclass(frozen=True, kw_only=True)
class DeclaredRestriction(ValueObject):
    """One user-declared movement restriction or exercise contraindication
    on file — e.g. `DeclaredRestriction(tag="overhead_pressing")` for a
    known shoulder issue. Deliberately a small, caller-supplied tag, not a
    reference into `app.domain.exercise`'s `contraindication_tags`
    (Exercise's own key attribute) — matching those tags against a
    specific exercise list is an Exercise Recommendation / Substitution
    concern, explicitly out of scope for this phase (`Do NOT implement:
    Exercise substitution`). `ContraindicationRule` below can only say
    "this restriction is on file", never "this specific exercise is
    unsafe" — see that rule's own docstring.
    """

    tag: str
    description: str = ""

    def __post_init__(self) -> None:
        ensure_not_empty(self.tag, "declared restriction tag")


@dataclass(frozen=True, kw_only=True)
class ActiveInjury(ValueObject):
    """One active injury or rehabilitation restriction on file — the
    Product Bible's "Injury/medical screening: structured questions plus
    clinician-clearance flags before risky movement categories unlock"
    (MVP, "non-negotiable"). `restricts_training` mirrors that
    clinician-clearance gate: `True` until an explicit clearance is
    recorded elsewhere (a future application-layer concern — this
    package receives whatever `restricts_training` value the caller
    already determined, it does not compute or store clearance state
    itself).
    """

    description: str
    restricts_training: bool = True

    def __post_init__(self) -> None:
        ensure_not_empty(self.description, "active injury description")


@dataclass(frozen=True, kw_only=True)
class SafetyRuleContext(RuleContext):
    """One evaluation's worth of safety data: an optional readiness
    snapshot, an optional recent-training history, and whatever
    restrictions/injuries the caller already knows about (empty tuples by
    default — a real, evaluable fact, "confirmed none declared", not
    "unknown"; contrast with the `None` defaults on `readiness`/
    `recent_training`, each of which genuinely means "not supplied,
    cannot evaluate" since a missing check-in or session history is not
    the same claim as a confirmed-empty one).
    """

    readiness: ReadinessContext | None = None
    recent_training: ProgressiveOverloadRuleContext | None = None
    declared_restrictions: tuple[DeclaredRestriction, ...] = field(default_factory=tuple)
    active_injuries: tuple[ActiveInjury, ...] = field(default_factory=tuple)
