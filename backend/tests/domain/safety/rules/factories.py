"""Shared test helpers for the Safety Rule Engine's test suite.

Not itself a test file (no `test_` prefix, so pytest never collects it) —
mirrors `tests/domain/goal/rules/factories.py`'s reasoning exactly.
"""

from __future__ import annotations

from datetime import date

from app.domain.readiness.context import ReadinessContext
from app.domain.readiness.enums import ReadinessSource
from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.value_objects import (
    EnergyLevel,
    HeartRateVariability,
    ReadinessDate,
    RecoveryNotes,
    RestingHeartRate,
    SleepDuration,
    SleepQuality,
    SorenessLevel,
    StressLevel,
)
from app.domain.safety.rules.context import ActiveInjury, DeclaredRestriction, SafetyRuleContext
from app.domain.user.identifiers import UserId
from app.domain.workout.rules.context import ProgressiveOverloadRuleContext


def a_readiness_context(
    *,
    readiness_id: ReadinessId | None = None,
    user_id: UserId | None = None,
    readiness_date: ReadinessDate | None = None,
    source: ReadinessSource | None = None,
    sleep_duration: SleepDuration | None = None,
    sleep_quality: SleepQuality | None = None,
    energy_level: EnergyLevel | None = None,
    stress_level: StressLevel | None = None,
    soreness_level: SorenessLevel | None = None,
    resting_heart_rate: RestingHeartRate | None = None,
    heart_rate_variability: HeartRateVariability | None = None,
    notes: RecoveryNotes | None = None,
) -> ReadinessContext:
    """A `ReadinessContext` built directly (not via a live `Readiness`
    aggregate) — every field this package's rules read is directly
    overridable, the same reasoning `tests/domain/goal/rules/factories.py`'s
    `a_goal_context()` documents."""
    return ReadinessContext(
        readiness_id=readiness_id or ReadinessId.generate(),
        user_id=user_id or UserId.generate(),
        readiness_date=readiness_date or ReadinessDate(date(2026, 1, 1)),
        source=source,
        sleep_duration=sleep_duration,
        sleep_quality=sleep_quality,
        energy_level=energy_level,
        stress_level=stress_level,
        soreness_level=soreness_level,
        resting_heart_rate=resting_heart_rate,
        heart_rate_variability=heart_rate_variability,
        notes=notes or RecoveryNotes(),
    )


def a_declared_restriction(
    *, tag: str = "overhead_pressing", description: str = ""
) -> DeclaredRestriction:
    return DeclaredRestriction(tag=tag, description=description)


def an_active_injury(
    *, description: str = "Left shoulder strain", restricts_training: bool = True
) -> ActiveInjury:
    return ActiveInjury(description=description, restricts_training=restricts_training)


def a_safety_context(
    *,
    readiness: ReadinessContext | None = None,
    recent_training: ProgressiveOverloadRuleContext | None = None,
    declared_restrictions: tuple[DeclaredRestriction, ...] = (),
    active_injuries: tuple[ActiveInjury, ...] = (),
) -> SafetyRuleContext:
    """A `SafetyRuleContext` wrapping the given fields as-is — every
    field defaults to "nothing supplied", matching `SafetyRuleContext`'s
    own field defaults."""
    return SafetyRuleContext(
        readiness=readiness,
        recent_training=recent_training,
        declared_restrictions=declared_restrictions,
        active_injuries=active_injuries,
    )
