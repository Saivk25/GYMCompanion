"""Tests for app/application/shared/interfaces.py."""

import pytest

from app.application.shared.application_result import ApplicationResult
from app.application.shared.interfaces import Handler


@pytest.mark.unit
def test_handler_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        Handler()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_subclass_missing_handle_still_cannot_be_instantiated() -> None:
    class _IncompleteHandler(Handler[int, int]):
        pass

    with pytest.raises(TypeError):
        _IncompleteHandler()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_complete_subclass_can_be_instantiated_and_used() -> None:
    class _DoubleHandler(Handler[int, int]):
        def handle(self, request: int) -> ApplicationResult[int]:
            return ApplicationResult.ok(request * 2)

    handler = _DoubleHandler()
    result = handler.handle(21)
    assert result.success is True
    assert result.value == 42
