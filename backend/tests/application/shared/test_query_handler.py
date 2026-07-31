"""Tests for app/application/shared/query_handler.py."""

from dataclasses import dataclass

import pytest

from app.application.shared.application_result import ApplicationResult
from app.application.shared.interfaces import Handler
from app.application.shared.query import Query
from app.application.shared.query_handler import QueryHandler


@dataclass(frozen=True, kw_only=True)
class _GetThingQuery(Query):
    thing_id: str


@pytest.mark.unit
def test_query_handler_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        QueryHandler()  # type: ignore[abstract]


@pytest.mark.unit
def test_query_handler_is_a_handler() -> None:
    class _GetThingHandler(QueryHandler[_GetThingQuery, str]):
        def handle(self, query: _GetThingQuery) -> ApplicationResult[str]:
            return ApplicationResult.ok(query.thing_id)

    handler = _GetThingHandler()
    assert isinstance(handler, Handler)


@pytest.mark.unit
def test_a_complete_subclass_can_be_instantiated_and_used() -> None:
    class _GetThingHandler(QueryHandler[_GetThingQuery, str]):
        def handle(self, query: _GetThingQuery) -> ApplicationResult[str]:
            return ApplicationResult.ok(f"found {query.thing_id}")

    handler = _GetThingHandler()
    result = handler.handle(_GetThingQuery(thing_id="abc"))
    assert result.success is True
    assert result.value == "found abc"
