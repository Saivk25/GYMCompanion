"""Tests for app/domain/shared_kernel/service.py."""

import pytest

from app.domain.shared_kernel.service import DomainService


@pytest.mark.unit
def test_domain_service_is_subclassable_with_arbitrary_behavior() -> None:
    """No forced method signature — see the module docstring for why.
    This test exists to prove that's actually true, not just documented."""

    class _SafetyRuleEngine(DomainService):
        def evaluate(self, heart_rate: int) -> bool:
            return heart_rate < 180

    engine = _SafetyRuleEngine()
    assert engine.evaluate(150) is True
    assert engine.evaluate(200) is False
