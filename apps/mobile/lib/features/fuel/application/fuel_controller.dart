import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/fuel_models.dart';

/// The seam between Fuel's presentation layer and wherever its data
/// actually comes from — mirrors `TrainRepository`'s own role exactly
/// (`features/train/application/train_controller.dart`). [logMeal] maps
/// to `POST /api/v1/nutrition` (`RecordNutritionRequest`) with macro
/// fields populated; [logWater] maps to the same endpoint with only
/// `water_intake` populated — per `fuel_models.dart`'s own doc comment,
/// there is no separate water-logging endpoint, because there is no
/// separate water-logging *concept* on the backend.
///
/// There is deliberately no method here for food search or supplement
/// tracking — no backend endpoint exists for either
/// (`backend/app/api/routes/v1/` has no food-database or supplement
/// route at all), so `FoodSearchScreen` and `SupplementsScreen` render a
/// disclosed "not connected yet" state directly, the same posture
/// `TrainRepository` already established for personal records and the
/// exercise catalog. See `docs/adr/0038-fuel-module.md`.
abstract interface class FuelRepository {
  Future<FuelHomeViewState> fetchHome();

  Future<FuelEntry> logMeal({
    required DateTime date,
    MealType? mealType,
    double? calories,
    double? protein,
    double? carbohydrates,
    double? fat,
    double? fiber,
    double? sugar,
    String? notes,
  });

  Future<FuelEntry> logWater({required DateTime date, required double amountMl});
}

/// No default implementation — the same "throw until overridden" posture
/// [trainRepositoryProvider]/[todayRepositoryProvider] use.
final Provider<FuelRepository> fuelRepositoryProvider = Provider<FuelRepository>(
  (ref) => throw UnimplementedError(
    'fuelRepositoryProvider has no default implementation — see '
    'lib/main.dart, which overrides it with MockFuelRepository '
    'until a real API-backed repository exists.',
  ),
);

/// Fuel Home's page-level fetch lifecycle, plus its two logging actions.
/// Unlike `ActiveSessionController` (which owns many fine-grained
/// mutations against one session), Fuel Home only ever has two — log a
/// meal, log water — and both simply re-fetch afterward rather than
/// hand-merging the new entry into local state: `MockFuelRepository`'s
/// round trip is fast enough that a re-fetch already reads as the
/// Bible's own "appears at the top of today's list immediately"
/// (Section 5.10's Success state) without a second, parallel "insert at
/// the front" code path that could drift from what a real re-fetch
/// would actually show.
class FuelHomeController extends AsyncNotifier<FuelHomeViewState> {
  @override
  Future<FuelHomeViewState> build() {
    return ref.read(fuelRepositoryProvider).fetchHome();
  }

  Future<void> refresh() async {
    state = const AsyncValue<FuelHomeViewState>.loading();
    state = await AsyncValue.guard(() => ref.read(fuelRepositoryProvider).fetchHome());
  }

  /// Does *not* guard into `state` on failure — mirrors
  /// `ActiveSessionController`'s own reasoning exactly: a failed log
  /// should not blank Fuel Home behind a full-page error. It rethrows;
  /// `LogMealScreen`/`WaterLogSheet` catch locally and show a `SnackBar`.
  Future<void> logMeal({
    required DateTime date,
    MealType? mealType,
    double? calories,
    double? protein,
    double? carbohydrates,
    double? fat,
    double? fiber,
    double? sugar,
    String? notes,
  }) async {
    await ref.read(fuelRepositoryProvider).logMeal(
          date: date,
          mealType: mealType,
          calories: calories,
          protein: protein,
          carbohydrates: carbohydrates,
          fat: fat,
          fiber: fiber,
          sugar: sugar,
          notes: notes,
        );
    state = await AsyncValue.guard(() => ref.read(fuelRepositoryProvider).fetchHome());
  }

  Future<void> logWater({required DateTime date, required double amountMl}) async {
    await ref.read(fuelRepositoryProvider).logWater(date: date, amountMl: amountMl);
    state = await AsyncValue.guard(() => ref.read(fuelRepositoryProvider).fetchHome());
  }
}

final AsyncNotifierProvider<FuelHomeController, FuelHomeViewState> fuelHomeControllerProvider =
    AsyncNotifierProvider<FuelHomeController, FuelHomeViewState>(FuelHomeController.new);
