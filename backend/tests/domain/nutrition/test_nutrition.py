"""Tests for app/domain/nutrition/nutrition.py."""

from datetime import date, datetime, timezone

import pytest

from app.domain.nutrition.enums import MealType, NutritionSource
from app.domain.nutrition.events import (
    MealNotesUpdated,
    NutritionRecorded,
    NutritionUpdated,
    WaterUpdated,
)
from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.nutrition import Nutrition
from app.domain.nutrition.value_objects import (
    Calories,
    Carbohydrates,
    Fat,
    Fiber,
    MealNotes,
    NutritionDate,
    Protein,
    Sugar,
    WaterIntake,
)
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.user.identifiers import UserId
from tests.domain.nutrition.factories import a_fixed_clock, a_recorded_nutrition

# --- record() ---


@pytest.mark.unit
def test_record_exposes_the_required_fields_it_was_given() -> None:
    nutrition_id = NutritionId.generate()
    user_id = UserId.generate()
    nutrition = Nutrition.record(
        nutrition_id=nutrition_id,
        user_id=user_id,
        nutrition_date=NutritionDate(date(2026, 1, 1)),
        clock=a_fixed_clock(),
    )
    assert nutrition.id == nutrition_id
    assert nutrition.user_id == user_id
    assert nutrition.nutrition_date == NutritionDate(date(2026, 1, 1))


@pytest.mark.unit
def test_record_stamps_recorded_at_from_the_clock() -> None:
    clock = a_fixed_clock()
    nutrition = Nutrition.record(
        nutrition_id=NutritionId.generate(),
        user_id=UserId.generate(),
        nutrition_date=NutritionDate(date(2026, 1, 1)),
        clock=clock,
    )
    assert nutrition.recorded_at == clock.now()


@pytest.mark.unit
def test_record_defaults_every_optional_field_to_none_and_notes_to_empty() -> None:
    nutrition = a_recorded_nutrition()
    assert nutrition.meal_type is None
    assert nutrition.source is None
    assert nutrition.calories is None
    assert nutrition.protein is None
    assert nutrition.carbohydrates is None
    assert nutrition.fat is None
    assert nutrition.fiber is None
    assert nutrition.sugar is None
    assert nutrition.water_intake is None
    assert nutrition.notes == MealNotes()
    assert nutrition.updated_at is None


@pytest.mark.unit
def test_record_accepts_every_optional_field_at_once() -> None:
    nutrition = Nutrition.record(
        nutrition_id=NutritionId.generate(),
        user_id=UserId.generate(),
        nutrition_date=NutritionDate(date(2026, 1, 1)),
        clock=a_fixed_clock(),
        meal_type=MealType.LUNCH,
        source=NutritionSource.BARCODE,
        calories=Calories(600.0),
        protein=Protein(40.0),
        carbohydrates=Carbohydrates(60.0),
        fat=Fat(20.0),
        fiber=Fiber(10.0),
        sugar=Sugar(8.0),
        water_intake=WaterIntake(250.0),
        notes=MealNotes("Post-workout meal."),
    )
    assert nutrition.meal_type == MealType.LUNCH
    assert nutrition.source == NutritionSource.BARCODE
    assert nutrition.calories == Calories(600.0)
    assert nutrition.protein == Protein(40.0)
    assert nutrition.carbohydrates == Carbohydrates(60.0)
    assert nutrition.fat == Fat(20.0)
    assert nutrition.fiber == Fiber(10.0)
    assert nutrition.sugar == Sugar(8.0)
    assert nutrition.water_intake == WaterIntake(250.0)
    assert nutrition.notes == MealNotes("Post-workout meal.")


@pytest.mark.unit
def test_record_raises_a_nutrition_recorded_event() -> None:
    nutrition_id = NutritionId.generate()
    user_id = UserId.generate()
    nutrition_date = NutritionDate(date(2026, 1, 1))
    clock = a_fixed_clock()

    nutrition = Nutrition.record(
        nutrition_id=nutrition_id,
        user_id=user_id,
        nutrition_date=nutrition_date,
        clock=clock,
        meal_type=MealType.BREAKFAST,
        source=NutritionSource.MANUAL,
    )

    events = nutrition.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], NutritionRecorded)
    assert events[0].nutrition_id == nutrition_id
    assert events[0].user_id == user_id
    assert events[0].nutrition_date == nutrition_date
    assert events[0].meal_type == MealType.BREAKFAST
    assert events[0].source == NutritionSource.MANUAL
    assert events[0].occurred_at == clock.now()


@pytest.mark.unit
def test_record_raises_exactly_one_event_even_with_optional_fields_supplied() -> None:
    nutrition = Nutrition.record(
        nutrition_id=NutritionId.generate(),
        user_id=UserId.generate(),
        nutrition_date=NutritionDate(date(2026, 1, 1)),
        clock=a_fixed_clock(),
        calories=Calories(500.0),
        water_intake=WaterIntake(250.0),
        notes=MealNotes("hi"),
    )
    events = nutrition.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], NutritionRecorded)


@pytest.mark.unit
def test_record_generates_a_distinct_nutrition_each_time() -> None:
    assert a_recorded_nutrition().id != a_recorded_nutrition().id


# --- update_nutrition() ---


@pytest.mark.unit
def test_update_nutrition_sets_previously_unset_fields() -> None:
    nutrition = a_recorded_nutrition()
    nutrition.update_nutrition(calories=Calories(500.0), clock=a_fixed_clock())
    assert nutrition.calories == Calories(500.0)


@pytest.mark.unit
def test_update_nutrition_replaces_a_previously_set_field() -> None:
    nutrition = a_recorded_nutrition()
    clock = a_fixed_clock()
    nutrition.update_nutrition(calories=Calories(500.0), clock=clock)
    nutrition.update_nutrition(calories=Calories(450.0), clock=clock)
    assert nutrition.calories == Calories(450.0)


@pytest.mark.unit
def test_update_nutrition_accepts_zero_for_any_field() -> None:
    """Zero is legitimate — a fasting day, a food with no fat."""
    nutrition = a_recorded_nutrition()
    nutrition.update_nutrition(calories=Calories(0.0), fat=Fat(0.0), clock=a_fixed_clock())
    assert nutrition.calories == Calories(0.0)
    assert nutrition.fat == Fat(0.0)


@pytest.mark.unit
def test_update_nutrition_none_leaves_other_fields_unchanged() -> None:
    nutrition = a_recorded_nutrition()
    clock = a_fixed_clock()
    nutrition.update_nutrition(calories=Calories(500.0), protein=Protein(30.0), clock=clock)
    nutrition.update_nutrition(fat=Fat(15.0), clock=clock)
    assert nutrition.calories == Calories(500.0)
    assert nutrition.protein == Protein(30.0)
    assert nutrition.fat == Fat(15.0)


@pytest.mark.unit
def test_update_nutrition_all_six_fields_at_once() -> None:
    nutrition = a_recorded_nutrition()
    nutrition.update_nutrition(
        calories=Calories(500.0),
        protein=Protein(30.0),
        carbohydrates=Carbohydrates(50.0),
        fat=Fat(15.0),
        fiber=Fiber(8.0),
        sugar=Sugar(5.0),
        clock=a_fixed_clock(),
    )
    assert nutrition.calories == Calories(500.0)
    assert nutrition.protein == Protein(30.0)
    assert nutrition.carbohydrates == Carbohydrates(50.0)
    assert nutrition.fat == Fat(15.0)
    assert nutrition.fiber == Fiber(8.0)
    assert nutrition.sugar == Sugar(5.0)


@pytest.mark.unit
def test_update_nutrition_stamps_updated_at() -> None:
    nutrition = a_recorded_nutrition()
    clock = a_fixed_clock()
    nutrition.update_nutrition(calories=Calories(500.0), clock=clock)
    assert nutrition.updated_at == clock.now()


@pytest.mark.unit
def test_update_nutrition_records_event_with_full_resulting_snapshot() -> None:
    nutrition = a_recorded_nutrition()
    clock = a_fixed_clock()
    nutrition.update_nutrition(calories=Calories(500.0), protein=Protein(30.0), clock=clock)
    nutrition.pull_domain_events()  # drain NutritionRecorded

    nutrition.update_nutrition(fat=Fat(15.0), clock=clock)

    events = nutrition.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], NutritionUpdated)
    assert events[0].calories == Calories(500.0)
    assert events[0].protein == Protein(30.0)
    assert events[0].fat == Fat(15.0)
    assert events[0].carbohydrates is None


@pytest.mark.unit
def test_update_nutrition_is_freely_callable_with_no_lifecycle_gate() -> None:
    """Nutrition has no status enum — nothing blocks calling update
    methods repeatedly, unlike Workout/Exercise/WorkoutSession's
    terminal-state guards."""
    nutrition = a_recorded_nutrition()
    clock = a_fixed_clock()
    for value in (500.0, 480.0, 460.0):
        nutrition.update_nutrition(calories=Calories(value), clock=clock)
    assert nutrition.calories == Calories(460.0)


# --- update_water() ---


@pytest.mark.unit
def test_update_water_sets_water_intake() -> None:
    nutrition = a_recorded_nutrition()
    nutrition.update_water(WaterIntake(500.0), clock=a_fixed_clock())
    assert nutrition.water_intake == WaterIntake(500.0)


@pytest.mark.unit
def test_update_water_replaces_a_previously_set_value() -> None:
    nutrition = a_recorded_nutrition()
    clock = a_fixed_clock()
    nutrition.update_water(WaterIntake(500.0), clock=clock)
    nutrition.update_water(WaterIntake(750.0), clock=clock)
    assert nutrition.water_intake == WaterIntake(750.0)


@pytest.mark.unit
def test_update_water_accepts_zero() -> None:
    nutrition = a_recorded_nutrition()
    nutrition.update_water(WaterIntake(0.0), clock=a_fixed_clock())
    assert nutrition.water_intake == WaterIntake(0.0)


@pytest.mark.unit
def test_update_water_stamps_updated_at() -> None:
    nutrition = a_recorded_nutrition()
    clock = a_fixed_clock()
    nutrition.update_water(WaterIntake(500.0), clock=clock)
    assert nutrition.updated_at == clock.now()


@pytest.mark.unit
def test_update_water_records_a_water_updated_event() -> None:
    nutrition = a_recorded_nutrition()
    clock = a_fixed_clock()
    water_intake = WaterIntake(500.0)

    nutrition.update_water(water_intake, clock=clock)

    events = nutrition.pull_domain_events()
    assert len(events) == 2  # NutritionRecorded, then WaterUpdated
    assert isinstance(events[-1], WaterUpdated)
    assert events[-1].water_intake == water_intake
    assert events[-1].occurred_at == clock.now()


@pytest.mark.unit
def test_update_water_does_not_affect_other_macro_fields() -> None:
    nutrition = a_recorded_nutrition()
    clock = a_fixed_clock()
    nutrition.update_nutrition(calories=Calories(500.0), clock=clock)
    nutrition.update_water(WaterIntake(500.0), clock=clock)
    assert nutrition.calories == Calories(500.0)


# --- update_notes() ---


@pytest.mark.unit
def test_update_notes_replaces_the_notes() -> None:
    nutrition = a_recorded_nutrition()
    nutrition.update_notes(MealNotes("Post-workout meal."), clock=a_fixed_clock())
    assert nutrition.notes == MealNotes("Post-workout meal.")


@pytest.mark.unit
def test_update_notes_accepts_an_explicitly_empty_value() -> None:
    nutrition = a_recorded_nutrition()
    clock = a_fixed_clock()
    nutrition.update_notes(MealNotes("something"), clock=clock)
    nutrition.update_notes(MealNotes(""), clock=clock)
    assert nutrition.notes == MealNotes("")


@pytest.mark.unit
def test_update_notes_stamps_updated_at() -> None:
    nutrition = a_recorded_nutrition()
    clock = a_fixed_clock()
    nutrition.update_notes(MealNotes("x"), clock=clock)
    assert nutrition.updated_at == clock.now()


@pytest.mark.unit
def test_update_notes_records_a_meal_notes_updated_event() -> None:
    nutrition = a_recorded_nutrition()
    clock = a_fixed_clock()
    notes = MealNotes("Post-workout meal.")

    nutrition.update_notes(notes, clock=clock)

    events = nutrition.pull_domain_events()
    assert len(events) == 2  # NutritionRecorded, then MealNotesUpdated
    assert isinstance(events[-1], MealNotesUpdated)
    assert events[-1].notes == notes
    assert events[-1].occurred_at == clock.now()


# --- __init__ construction (repository rehydration path) ---


@pytest.mark.unit
def test_constructor_rejects_a_naive_recorded_at() -> None:
    with pytest.raises(DomainInvariantViolationError, match="timezone-aware"):
        Nutrition(
            NutritionId.generate(),
            user_id=UserId.generate(),
            nutrition_date=NutritionDate(date(2026, 1, 1)),
            recorded_at=datetime(2026, 1, 1),  # deliberately naive
        )


@pytest.mark.unit
def test_constructor_rehydrates_an_existing_entry_with_no_side_effects() -> None:
    """The path a repository uses to reconstruct a Nutrition entry already
    in storage — no event should be raised."""
    nutrition = Nutrition(
        NutritionId.generate(),
        user_id=UserId.generate(),
        nutrition_date=NutritionDate(date(2026, 1, 1)),
        recorded_at=datetime.now(timezone.utc),
        calories=Calories(500.0),
    )
    assert nutrition.pull_domain_events() == []
    assert nutrition.calories == Calories(500.0)


@pytest.mark.unit
def test_constructor_accepts_every_explicit_field() -> None:
    now = datetime.now(timezone.utc)
    nutrition = Nutrition(
        NutritionId.generate(),
        user_id=UserId.generate(),
        nutrition_date=NutritionDate(date(2026, 1, 1)),
        recorded_at=now,
        meal_type=MealType.DINNER,
        source=NutritionSource.IMPORT,
        calories=Calories(700.0),
        protein=Protein(45.0),
        carbohydrates=Carbohydrates(70.0),
        fat=Fat(25.0),
        fiber=Fiber(12.0),
        sugar=Sugar(10.0),
        water_intake=WaterIntake(300.0),
        notes=MealNotes("Rehydrated."),
        updated_at=now,
    )
    assert nutrition.meal_type == MealType.DINNER
    assert nutrition.source == NutritionSource.IMPORT
    assert nutrition.calories == Calories(700.0)
    assert nutrition.protein == Protein(45.0)
    assert nutrition.carbohydrates == Carbohydrates(70.0)
    assert nutrition.fat == Fat(25.0)
    assert nutrition.fiber == Fiber(12.0)
    assert nutrition.sugar == Sugar(10.0)
    assert nutrition.water_intake == WaterIntake(300.0)
    assert nutrition.notes == MealNotes("Rehydrated.")
    assert nutrition.updated_at == now
