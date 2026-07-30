"""Shared test helpers for the Goal Alignment Rule Engine's test suite.

Not itself a test file (no `test_` prefix, so pytest never collects it) —
mirrors `tests/domain/readiness/rules/factories.py`'s reasoning exactly.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from app.domain.goal.context import GoalContext
from app.domain.goal.enums import GoalStatus, GoalType
from app.domain.goal.identifiers import GoalId
from app.domain.goal.rules.context import GoalAlignmentRuleContext
from app.domain.goal.value_objects import (
    GoalDescription,
    GoalName,
    GoalNotes,
    Priority,
    TargetBodyFat,
    TargetDate,
    TargetStrength,
    TargetWeight,
)
from app.domain.progress.context import ProgressContext
from app.domain.progress.enums import MeasurementUnit, ProgressSource
from app.domain.progress.identifiers import ProgressId
from app.domain.progress.value_objects import (
    ArmMeasurement,
    BodyFatPercentage,
    BodyWeight,
    CalfMeasurement,
    ChestMeasurement,
    HipMeasurement,
    LeanBodyMass,
    MuscleMass,
    NeckMeasurement,
    ProgressDate,
    ProgressNotes,
    ThighMeasurement,
    WaistMeasurement,
)
from app.domain.shared_kernel.clock import FixedClock
from app.domain.user.identifiers import UserId

_A_FIXED_INSTANT = datetime(2026, 1, 1, tzinfo=timezone.utc)
_A_REFERENCE_DATE = date(2026, 1, 1)


def a_fixed_clock() -> FixedClock:
    """A `FixedClock` pinned to an arbitrary, fixed instant — deterministic
    and irrelevant to what any test in this package actually asserts about,
    beyond that `Clock.now()` was consulted rather than the system clock.
    """
    return FixedClock(_A_FIXED_INSTANT)


def a_goal_context(
    *,
    goal_id: GoalId | None = None,
    user_id: UserId | None = None,
    goal_type: GoalType = GoalType.LOSE_FAT,
    name: GoalName | None = None,
    target_date: TargetDate | None = None,
    status: GoalStatus = GoalStatus.ACTIVE,
    description: GoalDescription | None = None,
    target_weight: TargetWeight | None = None,
    target_body_fat: TargetBodyFat | None = None,
    target_strength: TargetStrength | None = None,
    priority: Priority | None = None,
    notes: GoalNotes | None = None,
) -> GoalContext:
    """A `GoalContext` built directly (not via a live `Goal` aggregate) —
    every field this package's rules read is directly overridable, which
    is what most tests in this package need; `test_context.py` covers the
    `Goal`-aggregate-backed construction path separately.
    """
    return GoalContext(
        goal_id=goal_id or GoalId.generate(),
        user_id=user_id or UserId.generate(),
        goal_type=goal_type,
        name=name or GoalName("Lose 5kg"),
        target_date=target_date or TargetDate(date(2026, 6, 1)),
        status=status,
        description=description,
        target_weight=target_weight,
        target_body_fat=target_body_fat,
        target_strength=target_strength,
        priority=priority,
        notes=notes or GoalNotes(),
    )


def a_progress_context(
    *,
    progress_id: ProgressId | None = None,
    user_id: UserId | None = None,
    progress_date: ProgressDate | None = None,
    unit: MeasurementUnit = MeasurementUnit.METRIC,
    source: ProgressSource = ProgressSource.MANUAL,
    body_weight: BodyWeight | None = None,
    body_fat_percentage: BodyFatPercentage | None = None,
    lean_body_mass: LeanBodyMass | None = None,
    muscle_mass: MuscleMass | None = None,
    waist: WaistMeasurement | None = None,
    chest: ChestMeasurement | None = None,
    hip: HipMeasurement | None = None,
    arm: ArmMeasurement | None = None,
    thigh: ThighMeasurement | None = None,
    calf: CalfMeasurement | None = None,
    neck: NeckMeasurement | None = None,
    notes: ProgressNotes | None = None,
) -> ProgressContext:
    """A `ProgressContext` built directly, the same reasoning as
    `a_goal_context()` above."""
    return ProgressContext(
        progress_id=progress_id or ProgressId.generate(),
        user_id=user_id or UserId.generate(),
        progress_date=progress_date or ProgressDate(date(2026, 1, 1)),
        unit=unit,
        source=source,
        body_weight=body_weight,
        body_fat_percentage=body_fat_percentage,
        lean_body_mass=lean_body_mass,
        muscle_mass=muscle_mass,
        waist=waist,
        chest=chest,
        hip=hip,
        arm=arm,
        thigh=thigh,
        calf=calf,
        neck=neck,
        notes=notes or ProgressNotes(),
    )


def a_goal_alignment_context(
    *,
    goal: GoalContext | None = None,
    progress: ProgressContext | None = None,
    reference_date: date = _A_REFERENCE_DATE,
) -> GoalAlignmentRuleContext:
    """A `GoalAlignmentRuleContext` with a default Active goal, no
    progress snapshot, and a fixed reference date — the common starting
    point most tests in this package build on."""
    return GoalAlignmentRuleContext(
        goal=goal or a_goal_context(),
        progress=progress,
        reference_date=reference_date,
    )
