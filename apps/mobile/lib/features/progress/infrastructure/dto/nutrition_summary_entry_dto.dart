import '../../../../core/mapping/mapping.dart';
import '../../domain/progress_models.dart';

/// A narrow read of `NutritionResponse` (`backend/app/api/schemas/
/// nutrition.py`) — only the three fields [NutritionDayTotal] is built
/// from (`nutrition_date`, `protein`, `water_intake`), per
/// `docs/adr/0045`'s "a DTO models what a feature consumes" rule.
/// Deliberately not `FuelEntryDto` reused across a feature boundary —
/// see `progress_models.dart`'s own library doc comment ("Why this file
/// also carries real nutrition/readiness trend types") for why Progress
/// owns this narrower view type and its own parsing independently of
/// Fuel's.
class NutritionSummaryEntryDto {
  const NutritionSummaryEntryDto({
    required this.nutritionDate,
    required this.protein,
    required this.waterIntake,
  });

  factory NutritionSummaryEntryDto.fromJson(Map<String, dynamic> json) {
    return NutritionSummaryEntryDto(
      nutritionDate: parseApiDate(json.requireString('nutrition_date')),
      protein: json.optionalDouble('protein'),
      waterIntake: json.optionalDouble('water_intake'),
    );
  }

  final DateTime nutritionDate;
  final double? protein;
  final double? waterIntake;
}

/// Many-to-one: several real `Nutrition` entries for the same date
/// collapse into one [NutritionDayTotal] — not a 1:1 `toDomain()` on the
/// DTO itself, so per `docs/adr/0045`'s own convention this is a small
/// top-level function in the same file instead. [today] is passed in
/// (rather than read via `DateTime.now()` internally) so this stays a
/// pure function, trivially testable without mocking the clock.
///
/// Builds exactly 7 [NutritionDayTotal]s, oldest first — [today] minus 6
/// days through [today] — mirroring `MockProgressRepository
/// ._seedNutritionWeek`'s own fixed-7-day-window shape exactly, so
/// `ProgressHomeViewState.nutritionWeek`'s own "always exactly 7
/// entries" doc comment stays true against real data too. A day with no
/// matching entries gets `proteinGrams: 0, waterMl: 0, hasAnyEntry:
/// false` — the sum of an empty list is `0`, but [hasAnyEntry] is what
/// distinguishes that from a real day that was logged and totalled zero,
/// per [NutritionDayTotal]'s own doc comment.
List<NutritionDayTotal> aggregateNutritionWeek(
  List<NutritionSummaryEntryDto> entries,
  DateTime today,
) {
  return List<NutritionDayTotal>.generate(7, (int i) {
    final DateTime date = today.subtract(Duration(days: 6 - i));
    final String dateKey = apiDateString(date);
    final List<NutritionSummaryEntryDto> dayEntries = entries
        .where((NutritionSummaryEntryDto e) => apiDateString(e.nutritionDate) == dateKey)
        .toList();

    final double protein = dayEntries.fold(
      0,
      (double sum, NutritionSummaryEntryDto e) => sum + (e.protein ?? 0),
    );
    final double water = dayEntries.fold(
      0,
      (double sum, NutritionSummaryEntryDto e) => sum + (e.waterIntake ?? 0),
    );

    return NutritionDayTotal(
      date: date,
      proteinGrams: protein,
      waterMl: water,
      hasAnyEntry: dayEntries.isNotEmpty,
    );
  });
}
