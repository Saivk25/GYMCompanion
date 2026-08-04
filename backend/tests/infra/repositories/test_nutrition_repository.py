"""Integration tests for `NutritionSqlRepository` against a real, migrated
Postgres database. See `test_progress_repository.py`'s module docstring for
the shared fixture/foreign-key convention these tests follow.
"""

from datetime import date, datetime, timezone

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.domain.nutrition.enums import MealType, NutritionSource
from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.nutrition import Nutrition
from app.domain.nutrition.value_objects import Calories, NutritionDate, Protein
from app.domain.shared_kernel.clock import FixedClock
from app.domain.user.identifiers import UserId
from app.domain.user.user import User
from app.domain.user.value_objects import AuthMethod, Locale, Timezone
from app.infra.database import tenant_scope
from app.infra.repositories.nutrition_repository import NutritionSqlRepository
from app.infra.repositories.user_repository import UserSqlRepository

_CLOCK = FixedClock(datetime(2026, 1, 1, tzinfo=timezone.utc))


def _create_user(session_factory: sessionmaker[Session]) -> UserId:
    user_id = UserId.generate()
    user = User.register(
        user_id=user_id,
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        auth_method=AuthMethod("password"),
        clock=_CLOCK,
    )
    with session_factory() as session:
        UserSqlRepository(session).add(user)
        session.commit()
    return user_id


@pytest.mark.integration
def test_add_and_get_round_trip(session_factory: sessionmaker[Session]) -> None:
    user_id = _create_user(session_factory)
    nutrition_id = NutritionId.generate()
    nutrition = Nutrition.record(
        nutrition_id=nutrition_id,
        user_id=user_id,
        nutrition_date=NutritionDate(date(2026, 1, 2)),
        clock=_CLOCK,
        meal_type=MealType.BREAKFAST,
        source=NutritionSource.MANUAL,
        calories=Calories(450.0),
        protein=Protein(30.0),
    )

    with session_factory() as session:
        NutritionSqlRepository(session).add(nutrition)
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        fetched = NutritionSqlRepository(session).get(nutrition_id)

    assert fetched is not None
    assert fetched.meal_type is MealType.BREAKFAST
    assert fetched.calories == Calories(450.0)
    assert fetched.protein == Protein(30.0)


@pytest.mark.integration
def test_mutation_persists_without_a_second_add_call(
    session_factory: sessionmaker[Session],
) -> None:
    user_id = _create_user(session_factory)
    nutrition_id = NutritionId.generate()
    nutrition = Nutrition.record(
        nutrition_id=nutrition_id,
        user_id=user_id,
        nutrition_date=NutritionDate(date(2026, 1, 2)),
        clock=_CLOCK,
    )

    with session_factory() as session:
        NutritionSqlRepository(session).add(nutrition)
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        repository = NutritionSqlRepository(session)
        fetched = repository.get(nutrition_id)
        assert fetched is not None
        fetched.update_nutrition(clock=_CLOCK, calories=Calories(600.0))
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        refetched = NutritionSqlRepository(session).get(nutrition_id)

    assert refetched is not None
    assert refetched.calories == Calories(600.0)


@pytest.mark.integration
def test_list_by_user_returns_only_that_users_entries(
    session_factory: sessionmaker[Session],
) -> None:
    user_a = _create_user(session_factory)
    user_b = _create_user(session_factory)

    for user_id in (user_a, user_a, user_b):
        nutrition = Nutrition.record(
            nutrition_id=NutritionId.generate(),
            user_id=user_id,
            nutrition_date=NutritionDate(date(2026, 1, 2)),
            clock=_CLOCK,
        )
        with session_factory() as session:
            NutritionSqlRepository(session).add(nutrition)
            session.commit()

    with session_factory() as session:
        entries_for_a = NutritionSqlRepository(session).list_by_user(user_a)

    assert len(entries_for_a) == 2
    assert all(entry.user_id == user_a for entry in entries_for_a)


@pytest.mark.integration
def test_remove_deletes_the_row(session_factory: sessionmaker[Session]) -> None:
    user_id = _create_user(session_factory)
    nutrition_id = NutritionId.generate()
    nutrition = Nutrition.record(
        nutrition_id=nutrition_id,
        user_id=user_id,
        nutrition_date=NutritionDate(date(2026, 1, 2)),
        clock=_CLOCK,
    )

    with session_factory() as session:
        repository = NutritionSqlRepository(session)
        repository.add(nutrition)
        session.commit()
        repository.remove(nutrition)
        session.commit()

    with session_factory() as session, tenant_scope(session, str(user_id)):
        assert NutritionSqlRepository(session).get(nutrition_id) is None
