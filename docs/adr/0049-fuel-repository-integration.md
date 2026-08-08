# ADR 0049: Fuel repository integration — Step 3, feature 4

- Status: accepted
- Date: 2026-08-08

## Context

Step 3 of `docs/adr/0042-production-integration-plan.md`'s fourth
feature: replace `MockFuelRepository` with a real, backend-backed
`ApiFuelRepository`, reusing `docs/adr/0045`'s shared mapping
convention exactly as established. Unlike Today and Train, this
integration required no domain-model reduction — `fuel_models.dart`'s
own doc comment already stated `FuelEntry` mirrors `NutritionResponse`
field-for-field, and research confirmed this was accurate before any
code was written: every `FuelEntry` field maps directly onto a real
`NutritionResponse` field, and `FuelRepository`'s existing interface
(`fetchHome`/`logMeal`/`logWater`) maps cleanly onto the real
`GET`/`POST /api/v1/nutrition` endpoints with no shape mismatch. No
domain/UI decision requiring a stop-and-ask came up this phase.

## Decision

**Two endpoints, no interface change.** `fetchHome()` →
`GET /api/v1/nutrition` (`ListNutritionHandler`), the full unfiltered
list, filtered to today's entries client-side (no backend date-range
filter exists — ADR 0042 Part 2's own "no pagination or filtering
exists anywhere" finding, reused rather than treated as a new gap).
`logMeal()`/`logWater()` both → `POST /api/v1/nutrition`
(`RecordNutritionHandler`) — per `fuel_models.dart`'s own doc comment,
there is no separate water-logging endpoint because there is no
separate water-logging *concept* on the backend; `logWater` sends a
body with only `water_intake` set.

**`FuelEntryDto` mirrors the full `NutritionResponse`**, per
`docs/adr/0045`'s "a DTO reads every real field" rule, the same
"consumes everything" posture `ReadinessEntryDto` (ADR 0047) already
established for a feature that owns its own full response shape.
`MealType`/`NutritionSource` both gained `fromWire` factories, reusing
the exact convention `ReadinessSource`/`WorkoutStatus`/`SessionStatus`
already established. `MealType` also gained a `toWire` getter — this
phase is the first real repository that writes a client-chosen enum
*into* a request body (`logMeal`'s `meal_type` field) rather than only
ever reading one out of a response, so an explicit inverse mapping is
written by hand rather than relied on `.name` coincidentally matching
the wire string.

**`NutritionRuleEngine` is never reimplemented or approximated
client-side.** `logMeal`'s real warnings come from `POST
/api/v1/nutrition`'s own `IdResponse.warnings` — the exact strings
`CaloriesRule`/`ProteinRule`/`CarbohydratesRule`/`FatRule`/`FiberRule`/
`HydrationRule` produced server-side, returned unchanged and pushed
into `CoachSignalLog` unchanged (`FuelHomeController.logMeal` — this
method's own code did not change; only the repository beneath it did).

**Logged entries are honest echoes, not second fetches.** `POST
/api/v1/nutrition` returns only `IdResponse{id, warnings}` — the same
constraint `ApiReadinessRepository.submitCheckIn`/
`ApiTrainRepository.startSession` already faced. Confirmed by reading
both call sites (`FuelHomeController.logMeal`/`.logWater`) that neither
reads the returned `FuelEntry`'s fields — both discard it and
immediately re-fetch `fetchHome()`. `source` is echoed as `null` on
both methods — neither request body ever sends a `source` field, and
`Nutrition.record()` (`backend/app/domain/nutrition/nutrition.py`)
defaults an omitted `source` to `None`, mirroring
`ApiReadinessRepository`'s identical reasoning exactly.

**One disclosed gap: `proteinConsistencyLabel` is always `null`.**
`ProteinRule` (`backend/app/domain/nutrition/rules/protein_rule.py`,
read in full) is a single-entry sanity check against a fixed 50-250 g
range, evaluated only at record time — its own docstring explicitly
disclaims being "a personalized macro target." No endpoint returns a
computed weekly consistency figure. `FuelHomeScreen` already guards on
this field being `null`, so no presentation change was needed. Filed as
`docs/TECH_DEBT.md`'s new TD-0008.

## Consequences

`MockFuelRepository` was not deleted — kept as `test/features/fuel/`'s
fixture, doc comment updated to disclose it is no longer the production
implementation, mirroring `MockTodayRepository`'s/
`MockReadinessRepository`'s/`MockTrainRepository`'s own updated doc
comments.

`docs/TECH_DEBT.md`'s new TD-0008 records the protein-consistency gap
and its trigger conditions, following TD-0006/TD-0007's own established
structure.

Not yet verified by execution — same disclosed constraint as every
prior phase (ADR 0002). `test/features/fuel/api_fuel_repository_test.dart`
(structurally verified but not executed) covers: `fetchHome`'s
today-filtering and full-field mapping including `MealType`/
`NutritionSource` enums, `logMeal`'s selective body construction (only
submitted fields, `meal_type` written via `toWire`, `source` always
omitted) and real-warning propagation, and `logWater`'s minimal
`water_intake`-only body.
