"""Tests for app/domain/workout/rules/progressive_overload_rule_engine.py."""

from datetime import date, timedelta

import pytest

from app.domain.rules.engine import RuleEngine
from app.domain.rules.result import RuleId
from app.domain.workout.rules.deload_rule import DeloadRule
from app.domain.workout.rules.frequency_rule import FrequencyRule
from app.domain.workout.rules.intensity_rule import IntensityRule
from app.domain.workout.rules.progression_rule import ProgressionRule
from app.domain.workout.rules.progressive_overload_rule_engine import ProgressiveOverloadRuleEngine
from app.domain.workout.rules.volume_rule import VolumeRule
from tests.domain.workout.rules.factories import a_context, a_summary


@pytest.mark.unit
def test_is_a_rule_engine() -> None:
    assert isinstance(ProgressiveOverloadRuleEngine(), RuleEngine)


@pytest.mark.unit
def test_default_construction_registers_all_five_rules() -> None:
    engine = ProgressiveOverloadRuleEngine()
    rule_types = {type(rule) for rule in engine.rules}
    expected_rule_types: set[type[object]] = {
        VolumeRule,
        IntensityRule,
        FrequencyRule,
        ProgressionRule,
        DeloadRule,
    }
    assert rule_types == expected_rule_types
    assert len(engine.rules) == 5


@pytest.mark.unit
def test_accepts_a_custom_rule_set() -> None:
    custom_rule = VolumeRule(rule_id=RuleId("custom.volume"))
    engine = ProgressiveOverloadRuleEngine([custom_rule])
    assert engine.rules == (custom_rule,)


# --- evaluate(): a healthy progression history ---


@pytest.mark.unit
def test_evaluating_a_healthy_progression_history_passes() -> None:
    sessions = [
        a_summary(
            session_date=date(2026, 1, 1 + 2 * i),
            total_volume=1000.0 + 100 * i,
            average_load=100.0 + i,
        )
        for i in range(8)
    ]
    context = a_context(sessions=sessions)

    result = ProgressiveOverloadRuleEngine().evaluate(context)

    assert result.passed is True
    assert result.triggered_rules == ()


# --- evaluate(): a stagnant, low-frequency, overloaded history ---


@pytest.mark.unit
def test_evaluating_a_problematic_history_triggers_the_relevant_rules() -> None:
    # 8 sessions, one every 14 days (low frequency), with perfectly flat
    # volume/load across the whole window. Flat means no *decline*, so
    # Volume/Intensity both pass; but flat also means no new peak (so
    # Progression triggers — a genuine plateau) and every session sits
    # at 100% of the historical peak volume with no lighter session in
    # between (so Deload triggers too). Frequency triggers independently
    # on the 14-day spacing.
    start = date(2026, 1, 1)
    sessions = [
        a_summary(
            session_date=start + timedelta(days=14 * i), total_volume=1000.0, average_load=100.0
        )
        for i in range(8)
    ]
    context = a_context(sessions=sessions)

    result = ProgressiveOverloadRuleEngine().evaluate(context)

    assert result.passed is False
    assert RuleId("progressive_overload.frequency") in result.triggered_rules
    assert RuleId("progressive_overload.progression") in result.triggered_rules
    assert RuleId("progressive_overload.deload") in result.triggered_rules


@pytest.mark.unit
def test_evaluating_a_short_history_mostly_passes() -> None:
    context = a_context(sessions=[a_summary(session_date=date(2026, 1, 1))])
    result = ProgressiveOverloadRuleEngine().evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_evaluating_an_empty_history_passes() -> None:
    context = a_context(sessions=[])
    result = ProgressiveOverloadRuleEngine().evaluate(context)
    assert result.passed is True


# --- determinism / side-effect freedom ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    sessions = [a_summary(session_date=date(2026, 1, i)) for i in range(1, 6)]
    context = a_context(sessions=sessions)
    engine = ProgressiveOverloadRuleEngine()
    assert engine.evaluate(context) == engine.evaluate(context)


@pytest.mark.unit
def test_evaluate_does_not_mutate_the_context() -> None:
    sessions = [a_summary(session_date=date(2026, 1, i)) for i in range(1, 6)]
    context = a_context(sessions=sessions)
    ProgressiveOverloadRuleEngine().evaluate(context)
    assert context.sessions == tuple(sessions)
