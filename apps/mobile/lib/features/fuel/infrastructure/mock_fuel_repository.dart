import '../application/fuel_controller.dart';
import '../domain/fuel_models.dart';

/// A placeholder [FuelRepository] — the same disclosed-limitation
/// posture `MockTodayRepository`/`MockTrainRepository` established.
/// Stateful like `MockTrainRepository` (not read-only like
/// `MockTodayRepository`): a logged meal or water entry must be visible
/// on the very next fetch, so this mock keeps an in-memory `List
/// <FuelEntry>`, mutated by [logMeal]/[logWater] and read back by
/// [fetchHome] — reset on every app restart, fully disclosed here rather
/// than silently behaving like a real backend.
class MockFuelRepository implements FuelRepository {
  MockFuelRepository() : _entries = _seedEntries();

  final List<FuelEntry> _entries;
  int _nextId = 100;

  static List<FuelEntry> _seedEntries() {
    final DateTime today = DateTime.now();
    return <FuelEntry>[
      FuelEntry(
        nutritionId: 'seed-1',
        nutritionDate: today,
        recordedAt: DateTime(today.year, today.month, today.day, 8, 15),
        mealType: MealType.breakfast,
        source: NutritionSource.manual,
        calories: 420,
        protein: 28,
        carbohydrates: 45,
        fat: 14,
        notes: 'Greek yogurt, oats, berries',
      ),
      FuelEntry(
        nutritionId: 'seed-2',
        nutritionDate: today,
        recordedAt: DateTime(today.year, today.month, today.day, 9, 0),
        waterIntake: 500,
      ),
    ];
  }

  @override
  Future<FuelHomeViewState> fetchHome() async {
    await _delay();
    final DateTime now = DateTime.now();
    final List<FuelEntry> today = _entries.where((e) => _isSameDay(e.nutritionDate, now)).toList()
      ..sort((a, b) => b.recordedAt.compareTo(a.recordedAt));

    return FuelHomeViewState(
      date: now,
      todayEntries: today,
      hasLoggedAnyMealEver: _entries.isNotEmpty,
      // A genuinely computed weekly consistency figure needs the
      // NutritionRuleEngine's own historical-trend logic
      // (`backend/app/domain/nutrition/rules`) — Progress-dashboard
      // territory the Bible itself places outside Fuel. This one line
      // is disclosed mock text, the same posture Today's own
      // `oneLineSummary` preview already established, not a computed
      // result.
      proteinConsistencyLabel: '4 of the last 7 days on target',
    );
  }

  @override
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
  }) async {
    await _delay(short: true);
    final FuelEntry entry = FuelEntry(
      nutritionId: 'entry-${_nextId++}',
      nutritionDate: date,
      recordedAt: DateTime.now(),
      mealType: mealType,
      source: NutritionSource.manual,
      calories: calories,
      protein: protein,
      carbohydrates: carbohydrates,
      fat: fat,
      fiber: fiber,
      sugar: sugar,
      notes: notes ?? '',
    );
    _entries.add(entry);
    return entry;
  }

  @override
  Future<FuelEntry> logWater({required DateTime date, required double amountMl}) async {
    await _delay(short: true);
    final FuelEntry entry = FuelEntry(
      nutritionId: 'entry-${_nextId++}',
      nutritionDate: date,
      recordedAt: DateTime.now(),
      source: NutritionSource.manual,
      waterIntake: amountMl,
    );
    _entries.add(entry);
    return entry;
  }

  static bool _isSameDay(DateTime a, DateTime b) =>
      a.year == b.year && a.month == b.month && a.day == b.day;

  /// See `MockTodayRepository`'s own doc comment for why this delay is
  /// deliberate, not decorative.
  Future<void> _delay({bool short = false}) {
    return Future<void>.delayed(Duration(milliseconds: short ? 80 : 300));
  }
}
