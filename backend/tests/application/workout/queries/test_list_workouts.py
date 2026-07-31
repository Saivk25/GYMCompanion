"""Tests for app/application/workout/queries/list_workouts.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.shared.query import Query
from app.application.workout.queries.list_workouts import ListWorkoutsQuery
from app.domain.user.identifiers import UserId


@pytest.mark.unit
def test_list_workouts_query_is_a_query() -> None:
    assert isinstance(ListWorkoutsQuery(user_id=UserId.generate()), Query)


@pytest.mark.unit
def test_list_workouts_query_exposes_its_user_id() -> None:
    user_id = UserId.generate()
    query = ListWorkoutsQuery(user_id=user_id)
    assert query.user_id == user_id


@pytest.mark.unit
def test_list_workouts_query_is_immutable() -> None:
    query = ListWorkoutsQuery(user_id=UserId.generate())
    with pytest.raises(FrozenInstanceError):
        query.user_id = UserId.generate()  # type: ignore[misc]
