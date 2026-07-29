# ADR 0011: Nutrition is a per-entry log, not a daily rollup — meal_type and source are optional

- Status: accepted
- Date: 2026-07-29

## Context

Sprint 2, Step 7 asked for a `Nutrition` aggregate: "the canonical
representation of a user's daily nutritional intake," with a flat set of
value objects (`Calories`, `Protein`, `Carbohydrates`, `Fat`, `Fiber`,
`Sugar`, `WaterIntake`, `MealNotes` — no list or collection type), a
`MealType` enum (`Breakfast`/`Lunch`/`Dinner`/`Snack`), and a
`NutritionSource` enum (`Manual`/`Barcode`/`Import`).

Two things needed a decision before writing code, both following the
pattern ADR 0006/0008/0009/0010 already established of naming an ambiguity
explicitly rather than picking a reading silently:

1. **Aggregate granularity.** The Goal's "daily nutritional intake"
   phrasing could mean either (a) one `Nutrition` record per calendar day,
   holding that day's totals, or (b) one `Nutrition` record per logged
   entry (a specific meal or snack), with "daily intake" describing what
   the aggregate *type* tracks collectively, not a literal one-record-per-
   day cardinality. The presence of `MealType` — which only makes sense
   attached to a specific eating occasion, not a whole day — points toward
   (b); nothing in the value object list supports (a) (no list-of-meals
   structure, unlike `WorkoutSession`'s `ExercisePerformance`/
   `ExerciseSet`).

2. **Field requiredness.** The task's own Rules list states "Nutrition
   date required" explicitly, but says nothing about `meal_type` or
   `source` being required — a real, noticeable asymmetry against ADR
   0010's `Progress`, where both "Progress date required" *and*
   "Measurement unit required" were spelled out explicitly as two separate
   rules.

The Domain Model & Decision Engine Bible's closest concept, `Meal`
(Section 4.9, Table 12), is "a single logged eating event" with `input_type`
(how it was captured) but no fixed meal-type classification and no exact
`NutritionSource` analog — consistent with reading (b) above, but not
dispositive on its own since this task's own scope is deliberately smaller
than the Bible's `Meal` (no AI assessment, no `FoodItem` references, no
Logged -> Assessed -> Confirmed/Disputed lifecycle).

## Decision

1. **One `Nutrition` record is one logged entry** (matching the Bible's
   `Meal`, "a single logged eating event"), not a rolled-up total for a
   calendar day. Computing "today's total calories" from a set of
   `Nutrition` records sharing a user and date is a future read-model's
   job — the same relationship `Progress` has to Progress Intelligence's
   trend computation (ADR 0010): this aggregate stores facts, a separate,
   not-yet-built layer summarizes them. This also matches every other
   aggregate introduced this sprint (`WorkoutSession`, `Progress`): one
   instance is one point-in-time fact, never a period rollup.

2. **`meal_type: MealType | None` and `source: NutritionSource | None` are
   both optional, defaulting to `None`.** Taken literally from the Rules
   list's silence on requiring either — the same "don't invent
   required-ness beyond what's explicitly stated" discipline applied
   throughout this sprint. Practically, this also fits reading (b) well:
   not every logged entry cleanly maps to one of the four `MealType`
   values (a whole-day estimate logged in one shot, a grazing pattern that
   doesn't fit a single meal), and `source` is pure provenance metadata a
   caller may not always have.

## Consequences

A future NutritionPattern-equivalent read model (Bible: "the rolling
weekly-consistency read model built from Meals") that wants a day's total
must query every `Nutrition` record for a user/date and sum the non-`None`
fields itself — `NutritionRepository` currently declares no such query
method (matching every other aggregate's minimal `get`/`add`/`remove`
shape), so that lookup capability is real, additional work for whichever
increment builds that read model, not something already provided here.

Because `meal_type` is optional, a future increment cannot assume every
`Nutrition` record is attributable to a specific meal when computing
per-meal-type breakdowns; `None` is a legitimate, expected value to filter
on or bucket separately, not a data-quality gap to paper over.

This aggregate's shape (one record per entry, both classification enums
optional) sets the pattern for how a future `Meal`-alignment increment
(adding AI assessment, `FoodItem` references, or the Logged -> Assessed ->
Confirmed/Disputed lifecycle) would extend `Nutrition` rather than
replace it: those are additive fields/states on the same per-entry shape,
not a change to how many records exist per day.
