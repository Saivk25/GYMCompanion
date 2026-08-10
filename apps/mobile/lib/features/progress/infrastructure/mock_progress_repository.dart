import '../application/progress_controller.dart';
import '../domain/progress_models.dart';

/// A placeholder [ProgressRepository] — the same disclosed-limitation
/// posture `MockTrainRepository`/`MockFuelRepository` established.
/// Stateful like both of those (not read-only like `MockTodayRepository`):
/// a logged measurement must be visible on the very next fetch, so this
/// mock keeps an in-memory `List<ProgressEntry>`, seeded with ten weekly
/// check-ins so the Transformation dashboard's rolling-average chart
/// never opens looking artificially bare — reset on every app restart,
/// fully disclosed here rather than silently behaving like a real
/// backend.
///
/// [_nutritionWeek]/[_readinessWeek] are separately seeded, fixed
/// 7-day windows — real-shaped derived data (a day's real summed
/// protein/water, a day's real raw sleep/HR/HRV), standing in for what
/// `GET /api/v1/nutrition`/`GET /api/v1/readiness` would return for the
/// last 7 days once a real repository replaces this one. They are not
/// read from `MockFuelRepository`'s own state — see `progress_models
/// .dart`'s library doc comment for why Progress owns this view
/// independently rather than reaching into Fuel's.
class MockProgressRepository implements ProgressRepository {
  MockProgressRepository()
      : _entries = _seedMeasurements(),
        _nutritionWeek = _seedNutritionWeek(),
        _readinessWeek = _seedReadinessWeek();

  final List<ProgressEntry> _entries;
  final List<NutritionDayTotal> _nutritionWeek;
  final List<ReadinessDayEntry> _readinessWeek;
  int _nextId = 100;
  bool _hasShownIllustrativeWarnings = false;

  static List<ProgressEntry> _seedMeasurements() {
    final DateTime today = DateTime.now();
    // Ten weekly check-ins, oldest first while building, then reversed —
    // a gentle, realistic downward weight drift with normal day-to-day
    // noise, never a perfectly smooth line (a perfectly smooth seeded
    // trend would itself misrepresent what real logged data looks like).
    final List<double> weeklyWeights = <double>[
      82.4, 82.1, 81.9, 82.3, 81.6, 81.2, 81.4, 80.9, 80.6, 80.8,
    ];
    final List<ProgressEntry> entries = <ProgressEntry>[];
    for (int i = 0; i < weeklyWeights.length; i++) {
      final int weeksAgo = weeklyWeights.length - 1 - i;
      final DateTime date = today.subtract(Duration(days: weeksAgo * 7));
      entries.add(
        ProgressEntry(
          progressId: 'seed-progress-$i',
          progressDate: date,
          recordedAt: date,
          unit: 'metric',
          source: 'manual',
          bodyWeight: weeklyWeights[i],
          bodyFatPercentage: i.isEven ? 22.0 - (i * 0.15) : null,
          waist: i.isEven ? 86.0 - (i * 0.2) : null,
        ),
      );
    }
    return entries.reversed.toList(); // newest first
  }

  static List<NutritionDayTotal> _seedNutritionWeek() {
    final DateTime today = DateTime.now();
    final List<double> protein = <double>[118, 142, 135, 96, 150, 128, 145];
    final List<double> water = <double>[1800, 2100, 1950, 1400, 2300, 2000, 2200];
    return List<NutritionDayTotal>.generate(7, (int i) {
      final DateTime date = today.subtract(Duration(days: 6 - i));
      return NutritionDayTotal(
        date: date,
        proteinGrams: protein[i],
        waterMl: water[i],
        hasAnyEntry: true,
      );
    });
  }

  static List<ReadinessDayEntry> _seedReadinessWeek() {
    final DateTime today = DateTime.now();
    final List<double> sleep = <double>[7.2, 6.5, 7.8, 6.9, 7.1, 8.0, 7.4];
    final List<double> restingHr = <double>[54, 57, 53, 58, 55, 52, 54];
    final List<double> hrv = <double>[62, 55, 68, 51, 60, 71, 65];
    return List<ReadinessDayEntry>.generate(7, (int i) {
      final DateTime date = today.subtract(Duration(days: 6 - i));
      return ReadinessDayEntry(
        date: date,
        hasAnyEntry: true,
        sleepHours: sleep[i],
        restingHeartRate: restingHr[i],
        heartRateVariability: hrv[i],
      );
    });
  }

  @override
  Future<ProgressHomeViewState> fetchHome() async {
    await _delay();
    final List<ProgressEntry> sorted = List<ProgressEntry>.of(_entries)
      ..sort((ProgressEntry a, ProgressEntry b) => b.progressDate.compareTo(a.progressDate));

    return ProgressHomeViewState(
      asOf: DateTime.now(),
      measurements: sorted,
      nutritionWeek: _nutritionWeek,
      readinessWeek: _readinessWeek,
      hasLoggedAnyMeasurementEver: _entries.isNotEmpty,
    );
  }

  @override
  Future<ProgressLogResult> logMeasurement({
    required DateTime date,
    double? bodyWeight,
    double? bodyFatPercentage,
    double? leanBodyMass,
    double? muscleMass,
    double? waist,
    double? chest,
    double? hip,
    double? arm,
    double? thigh,
    double? calf,
    double? neck,
    String? notes,
  }) async {
    await _delay(short: true);
    final ProgressEntry entry = ProgressEntry(
      progressId: 'entry-${_nextId++}',
      progressDate: date,
      recordedAt: DateTime.now(),
      unit: 'metric',
      source: 'manual',
      bodyWeight: bodyWeight,
      bodyFatPercentage: bodyFatPercentage,
      leanBodyMass: leanBodyMass,
      muscleMass: muscleMass,
      waist: waist,
      chest: chest,
      hip: hip,
      arm: arm,
      thigh: thigh,
      calf: calf,
      neck: neck,
      notes: notes ?? '',
    );
    _entries.add(entry);

    // Two fixed, clearly-illustrative advisory strings on the first
    // logged measurement only, never a reimplementation of
    // `ProgressEvaluationRuleEngine`'s real consistency/plateau/trend
    // thresholds — the same disclosed posture
    // `MockReadinessRepository.submitCheckIn` already established; see
    // that file's own doc comment for the full reasoning, which applies
    // unchanged here.
    List<String> warnings = const <String>[];
    if (!_hasShownIllustrativeWarnings) {
      _hasShownIllustrativeWarnings = true;
      warnings = const <String>[
        '[advisory] Example advisory — real recommendations come from the '
            'backend progress-evaluation rule engine once connected.',
        '[warning] This illustrates where trend advice appears; it is not '
            'computed from the values you just entered.',
      ];
    }

    return ProgressLogResult(entry: entry, warnings: warnings);
  }

  /// See `MockTodayRepository`'s own doc comment for why this delay is
  /// deliberate, not decorative.
  Future<void> _delay({bool short = false}) {
    return Future<void>.delayed(Duration(milliseconds: short ? 80 : 300));
  }
}
