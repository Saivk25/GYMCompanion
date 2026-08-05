"""Tests for `build_rule_engines()`/`RuleEngines` — every registered
engine actually constructs, `.all()` matches the field count, and two
independent calls to `build_rule_engines()` produce independent objects
(proving this is a plain factory function, not a hidden singleton)."""

from __future__ import annotations

import pytest

from app.composition.rule_engines import RuleEngines, build_rule_engines
from app.domain.rules.engine import RuleEngine

_EXPECTED_FIELD_COUNT = 8


@pytest.mark.unit
def test_build_rule_engines_returns_a_fully_populated_registry() -> None:
    engines = build_rule_engines()
    assert isinstance(engines, RuleEngines)
    assert len(engines.all()) == _EXPECTED_FIELD_COUNT
    assert all(isinstance(engine, RuleEngine) for engine in engines.all())


@pytest.mark.unit
def test_every_engine_is_a_distinct_instance() -> None:
    engines = build_rule_engines()
    assert len({id(engine) for engine in engines.all()}) == _EXPECTED_FIELD_COUNT


@pytest.mark.unit
def test_two_calls_produce_independent_registries() -> None:
    first = build_rule_engines()
    second = build_rule_engines()
    assert first.safety is not second.safety
    assert first.readiness is not second.readiness


@pytest.mark.unit
def test_each_named_field_is_reachable_via_all() -> None:
    engines = build_rule_engines()
    named = {
        engines.exercise_recommendation,
        engines.goal_alignment,
        engines.nutrition,
        engines.progress_evaluation,
        engines.progressive_overload,
        engines.readiness,
        engines.safety,
        engines.training_load,
    }
    assert named == set(engines.all())
