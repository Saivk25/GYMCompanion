"""Tests for app/domain/training_load/rules/training_load_rule_engine.py."""

from datetime import date, timedelta

import pytest

from app.domain.rules.engine import RuleEngine
from app.domain.rules.result import RuleId
from app.domain.training_load.rules.acute_load_rule import AcuteLoadRule
from app.domain.training_load.rules.chronic_load_rule import ChronicLoadRule
from app.domain.training_load.rules.context import TrainingLoadRuleContext
from app.domain.training_load.rules.load_ratio_rule import LoadRatioRule
from app.domain.training_load.rules.monotony_rule import MonotonyRule
from app.domain.training_load.rules.strain_rule import StrainRule
from app.domain.training_load.rules.training_load_rule_engine import TrainingLoadRuleEngine
from tests.domain.training_load.rules.factories import daily_summaries


@pytest.mark.unit
def test_is_a_rule_engine() -> None:
    assert isinstance(TrainingLoadRuleEngine(), RuleEngine)


@pytest.mark.unit
def test_default_construction_registers_all_five_rules() -> None:
    engine = TrainingLoadRuleEngine()
    rule_types = {type(rule) for rule in engine.rules}
    expected_rule_types: set[type[object]] = {
        AcuteLoadRule,
        ChronicLoadRule,
        LoadRatioRule,
        MonotonyRule,
        StrainRule,
    }
    assert rule_types == expected_rule_types
    assert len(engine.rules) == 5


@pytest.mark.unit
def test_accepts_a_custom_rule_set() -> None:
    custom_rule = AcuteLoadRule(rule_id=RuleId("custom.acute_load"))
    engine = TrainingLoadRuleEngine([custom_rule])
    assert engine.rules == (custom_rule,)


# --- evaluate(): a fully healthy history ---


@pytest.mark.unit
def test_evaluating_an_empty_context_passes() -> None:
    result = TrainingLoadRuleEngine().evaluate(TrainingLoadRuleContext(history=()))
    assert result.passed is True
    assert result.triggered_rules == ()


@pytest.mark.unit
def test_evaluating_a_moderate_varied_history_passes() -> None:
    context = TrainingLoadRuleContext.from_summaries(
        daily_summaries(
            [300.0, 100.0, 350.0, 80.0, 250.0, 50.0, 200.0] * 4  # 28 days of varied load
        )
    )
    result = TrainingLoadRuleEngine().evaluate(context)
    assert result.passed is True


# --- evaluate(): multiple findings at once ---


@pytest.mark.unit
def test_evaluating_a_monotonous_spiking_history_triggers_several_rules() -> None:
    # 21 days of moderate constant load, then a 7-day spike to a much higher
    # constant load — should trip acute load, load ratio, and monotony/strain
    # (identical daily load within the trailing window).
    start = date(2026, 1, 1)
    history = daily_summaries([500.0] * 21, start_date=start) + daily_summaries(
        [2000.0] * 7, start_date=start + timedelta(days=21)
    )
    context = TrainingLoadRuleContext.from_summaries(history)

    result = TrainingLoadRuleEngine().evaluate(context)

    assert result.passed is False
    assert RuleId("training_load.acute_load") in result.triggered_rules
    assert RuleId("training_load.load_ratio") in result.triggered_rules
    assert RuleId("training_load.monotony") in result.triggered_rules
    assert RuleId("training_load.strain") in result.triggered_rules


# --- determinism / side-effect freedom ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    context = TrainingLoadRuleContext.from_summaries(daily_summaries([500.0] * 7))
    engine = TrainingLoadRuleEngine()
    assert engine.evaluate(context) == engine.evaluate(context)


@pytest.mark.unit
def test_evaluate_does_not_mutate_the_context() -> None:
    history = tuple(daily_summaries([500.0] * 7))
    context = TrainingLoadRuleContext(history=history)
    TrainingLoadRuleEngine().evaluate(context)
    assert context.history == history
