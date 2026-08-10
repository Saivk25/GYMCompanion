import '../../../core/cache/cache.dart';
import '../../../core/mapping/mapping.dart';
import '../../../core/network/network.dart';
import '../application/fuel_controller.dart';
import '../domain/fuel_models.dart';
import 'dto/fuel_entry_dto.dart';

/// The real [FuelRepository] — the fourth `ApiXRepository` this project
/// has built (`docs/adr/0049-fuel-repository-integration.md`), on the
/// same `ApiClient` (`docs/adr/0043`) and shared mapping convention
/// (`docs/adr/0045`) Today/Readiness/Train already proved. Wired in
/// `lib/main.dart`, replacing [MockFuelRepository]; `FuelHomeController`
/// and every Fuel screen are unchanged — same "swap the provider
/// override" seam every prior feature has used.
///
/// ## Two real endpoints, no interface change
///
/// [fetchHome] → `GET /api/v1/nutrition` (`ListNutritionHandler`), the
/// full unfiltered list, filtered to today's entries client-side (no
/// backend date-range filter exists — ADR 0042 Part 2's own "no
/// pagination or filtering exists anywhere" finding, reused here rather
/// than treated as a new gap). [logMeal]/[logWater] both →
/// `POST /api/v1/nutrition` (`RecordNutritionHandler`) — per
/// `fuel_models.dart`'s own doc comment, there is no separate
/// water-logging endpoint because there is no separate water-logging
/// *concept* on the backend; `logWater` sends a body with only
/// `water_intake` set, exactly mirroring what [MockFuelRepository]
/// already modeled. `FuelRepository`'s own interface did not change.
///
/// ## `NutritionRuleEngine` is never reimplemented or approximated
/// client-side
///
/// `logMeal`'s real warnings come from `POST /api/v1/nutrition`'s own
/// `IdResponse.warnings` — the exact strings `CaloriesRule`/
/// `ProteinRule`/`CarbohydratesRule`/`FatRule`/`FiberRule`/
/// `HydrationRule` produced server-side, returned unchanged. Nothing
/// here inspects a submitted macro against a threshold.
///
/// ## Logged entries are honest echoes, not second fetches
///
/// `POST /api/v1/nutrition` returns only `IdResponse{id, warnings}`
/// (`backend/app/api/schemas/common.py`'s own "deliberately not the
/// full updated resource" doc comment) — the same constraint
/// `ApiReadinessRepository.submitCheckIn` already faced. No current
/// caller reads the returned [FuelEntry] from either method
/// (`FuelHomeController.logMeal`/`.logWater` both discard it and
/// immediately re-fetch [fetchHome] instead — confirmed by reading both
/// call sites), so the entry each method returns is built from exactly
/// the parameters the caller passed plus the real `id` the backend
/// assigned. `source` is echoed as `null` on both — neither method's
/// request body ever sends a `source` field, and `Nutrition.record()`
/// (`backend/app/domain/nutrition/nutrition.py`) defaults an omitted
/// `source` to `None`, never `MANUAL`, mirroring
/// `ApiReadinessRepository`'s identical `source` reasoning exactly.
/// `recordedAt` is a local `DateTime.now()` approximation, not the
/// authoritative server-assigned timestamp — disclosed here as such,
/// harmless while unused.
///
/// ## One disclosed gap: `proteinConsistencyLabel`
///
/// Always `null` — `ProteinRule` (`backend/app/domain/nutrition/rules/
/// protein_rule.py`) is a single-entry sanity check evaluated only at
/// record time, never a stored or queryable weekly aggregate, and no
/// endpoint anywhere returns a computed "N of the last 7 days on
/// target" figure. Computing one client-side would mean inventing a
/// personalized macro target this backend does not model at all (that
/// rule's own docstring: "a wide, generic single-day sanity range...
/// not a personalized macro target") — exactly the "never duplicate
/// backend business logic" violation this phase's own instructions
/// forbid. `FuelHomeScreen` already guards on this field being `null`
/// (`if (state.proteinConsistencyLabel != null)`), so no presentation
/// change was needed. See `docs/TECH_DEBT.md`'s TD-0008.
///
/// ## `fetchHome` is now read-through cached (Step 4)
///
/// `docs/adr/0052-offline-caching.md` — [fetchHome] reuses the shared
/// `readThroughCache` policy (`core/cache/read_through_cache.dart`):
/// serves a fresh-enough cached response immediately while revalidating
/// in the background, falls back to the last cached response on a real
/// network failure ([FuelHomeViewState.isOffline] now genuinely reflects
/// this rather than always being `false`), and otherwise fetches live
/// and writes through. [logMeal]/[logWater] are mutations, not reads —
/// deliberately not cached, per this phase's own scope. Both do,
/// however, invalidate [fetchHome]'s own cache entry on success
/// (`LocalCache.invalidate`) so `FuelHomeController`'s existing mutate-
/// then-refetch call sites see the real new entry instead of a stale
/// cached list.
class ApiFuelRepository implements FuelRepository {
  ApiFuelRepository(this._client, this._cache);

  final ApiClient _client;
  final LocalCache _cache;

  static const String _cacheKey = 'fuel_home';

  @override
  Future<FuelHomeViewState> fetchHome() {
    return readThroughCache<FuelHomeViewState>(
      cache: _cache,
      key: _cacheKey,
      maxAge: kCacheFreshDuration,
      fetchRawJson: () => _client.getList('${ApiConfig.v1PathPrefix}/nutrition'),
      build: _buildViewState,
    );
  }

  FuelHomeViewState _buildViewState(Object? rawJson, {required bool isOffline}) {
    final List<FuelEntry> entries = (rawJson! as List<dynamic>)
        .cast<Map<String, dynamic>>()
        .map(FuelEntryDto.fromJson)
        .map((FuelEntryDto dto) => dto.toDomain())
        .toList(growable: false);

    final DateTime now = DateTime.now();
    final String todayKey = apiDateString(now);
    final List<FuelEntry> todayEntries = entries
        .where((FuelEntry e) => apiDateString(e.nutritionDate) == todayKey)
        .toList()
      ..sort((FuelEntry a, FuelEntry b) => b.recordedAt.compareTo(a.recordedAt));

    return FuelHomeViewState(
      date: now,
      todayEntries: todayEntries,
      hasLoggedAnyMealEver: entries.isNotEmpty,
      // No endpoint returns a computed weekly consistency figure — see
      // this class's own doc comment.
      proteinConsistencyLabel: null,
      isOffline: isOffline,
    );
  }

  @override
  Future<FuelLogResult> logMeal({
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
    final Map<String, dynamic> body = <String, dynamic>{
      'nutrition_date': apiDateString(date),
      if (mealType != null) 'meal_type': mealType.toWire,
      if (calories != null) 'calories': calories,
      if (protein != null) 'protein': protein,
      if (carbohydrates != null) 'carbohydrates': carbohydrates,
      if (fat != null) 'fat': fat,
      if (fiber != null) 'fiber': fiber,
      if (sugar != null) 'sugar': sugar,
      if (notes != null) 'notes': notes,
    };

    final Map<String, dynamic> json = await _client.post(
      '${ApiConfig.v1PathPrefix}/nutrition',
      body: body,
    );
    final String nutritionId = json.requireString('id');
    final List<String> warnings =
        (json.optionalList('warnings') ?? const <dynamic>[]).cast<String>();

    // `FuelHomeController.logMeal` refetches `fetchHome()` immediately
    // after this returns and expects the new entry to be there — see
    // `LocalCache.invalidate`'s own doc comment.
    await _cache.invalidate(_cacheKey);

    final FuelEntry entry = FuelEntry(
      nutritionId: nutritionId,
      nutritionDate: date,
      recordedAt: DateTime.now(),
      mealType: mealType,
      source: null,
      calories: calories,
      protein: protein,
      carbohydrates: carbohydrates,
      fat: fat,
      fiber: fiber,
      sugar: sugar,
      notes: notes ?? '',
    );

    return FuelLogResult(entry: entry, warnings: warnings);
  }

  @override
  Future<FuelEntry> logWater({required DateTime date, required double amountMl}) async {
    final Map<String, dynamic> json = await _client.post(
      '${ApiConfig.v1PathPrefix}/nutrition',
      body: <String, dynamic>{
        'nutrition_date': apiDateString(date),
        'water_intake': amountMl,
      },
    );
    final String nutritionId = json.requireString('id');

    // `FuelHomeController.logWater` refetches `fetchHome()` immediately
    // after this returns and expects the new entry to be there — see
    // `LocalCache.invalidate`'s own doc comment.
    await _cache.invalidate(_cacheKey);

    return FuelEntry(
      nutritionId: nutritionId,
      nutritionDate: date,
      recordedAt: DateTime.now(),
      source: null,
      waterIntake: amountMl,
    );
  }
}
