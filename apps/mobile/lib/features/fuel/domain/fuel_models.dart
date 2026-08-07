/// Pure Dart value types for the Fuel (Nutrition) module — no Flutter
/// import anywhere in this file, matching `features/today/domain/
/// today_models.dart` and `features/train/domain/train_models.dart`'s
/// own rule. Naming mirrors `backend/app/api/schemas/nutrition.py`'s
/// `NutritionResponse` field-for-field, and the two backend enums
/// (`app/domain/nutrition/enums.py`'s `MealType`, `NutritionSource`), so
/// a future real `FuelRepository` mapping API responses onto these types
/// is a direct translation, not a re-interpretation.
///
/// ## Why one `FuelEntry`, not a `Meal` type and a separate `WaterLog` type
///
/// `docs/adr/0011-nutrition-is-a-per-entry-log-not-a-daily-rollup.md`
/// (backend) already decided this: `Nutrition` is one per-entry log
/// where meal macros and `water_intake` are both optional fields on the
/// *same* record shape — logging water is just a `Nutrition` entry with
/// only `waterIntake` set and every macro field `null`. `FuelEntry`
/// carries that decision through unchanged rather than inventing a
/// client-side split the backend itself doesn't have. A day's total
/// water is the *sum* of every entry's `waterIntake` for that date, not
/// a single running counter — this is what "per-entry log, not a daily
/// rollup" means applied to hydration specifically.
library;

/// Which meal of the day an entry is associated with, when known
/// (`MealType | None` on the backend — not every entry cleanly maps to
/// one of these four).
enum MealType {
  breakfast,
  lunch,
  dinner,
  snack;

  String get label => switch (this) {
        MealType.breakfast => 'Breakfast',
        MealType.lunch => 'Lunch',
        MealType.dinner => 'Dinner',
        MealType.snack => 'Snack',
      };
}

/// How an entry's values were obtained. Every entry this module creates
/// today is [manual] — there is no barcode scanner or import pipeline
/// wired up yet, so [barcode]/[import] exist here only for API-shape
/// fidelity, not because any screen offers them.
enum NutritionSource { manual, barcode, import }

/// One logged entry — a meal, a water-only log, or both at once
/// (mirrors `NutritionResponse` exactly).
class FuelEntry {
  const FuelEntry({
    required this.nutritionId,
    required this.nutritionDate,
    required this.recordedAt,
    this.mealType,
    this.source,
    this.calories,
    this.protein,
    this.carbohydrates,
    this.fat,
    this.fiber,
    this.sugar,
    this.waterIntake,
    this.notes = '',
    this.updatedAt,
  });

  final String nutritionId;
  final DateTime nutritionDate;
  final DateTime recordedAt;
  final MealType? mealType;
  final NutritionSource? source;
  final double? calories;
  final double? protein;
  final double? carbohydrates;
  final double? fat;
  final double? fiber;
  final double? sugar;
  final double? waterIntake;
  final String notes;
  final DateTime? updatedAt;

  /// True once any macro field is populated — an entry can be
  /// water-only, in which case it belongs in a hydration total but never
  /// in a meal list (`FuelHomeScreen`'s own distinction).
  bool get isMeal =>
      calories != null || protein != null || carbohydrates != null || fat != null;

  bool get isWaterOnly => waterIntake != null && !isMeal;
}

/// The complete state Fuel Home renders from once its initial fetch has
/// resolved — mirrors `TrainHomeViewState`'s shape (a single page-level
/// `AsyncValue`, no nested per-card status enum: unlike Today's session
/// card, nothing on this page has its own independently-failing async
/// subsystem worth a narrower state machine).
class FuelHomeViewState {
  const FuelHomeViewState({
    required this.date,
    this.todayEntries = const <FuelEntry>[],
    this.hasLoggedAnyMealEver = true,
    this.proteinConsistencyLabel,
    this.isOffline = false,
  });

  final DateTime date;

  /// Every entry — meal and water-only — recorded for [date].
  final List<FuelEntry> todayEntries;

  /// `false` only for a brand-new user with no logging history at all —
  /// distinguishes the Bible's "first-use explainer of the three logging
  /// methods" (Section 5.10's Empty state) from the quieter "nothing
  /// logged *today* yet" case for a returning user, the same
  /// `hasActivePlan`-shaped distinction Today's own empty state makes.
  final bool hasLoggedAnyMealEver;

  /// The Bible's own phrase: "a one-line protein-consistency status for
  /// the week" (Section 5.10), or the empty-state row's exact wording,
  /// "not enough days logged yet" (Section 15), when there isn't enough
  /// history. `null` only while [hasLoggedAnyMealEver] is also `false`
  /// (a page with no history at all has no weekly line to show).
  final String? proteinConsistencyLabel;

  final bool isOffline;

  List<FuelEntry> get meals => todayEntries.where((e) => e.isMeal).toList();

  double get totalWaterMl =>
      todayEntries.fold(0, (double sum, FuelEntry e) => sum + (e.waterIntake ?? 0));
}
