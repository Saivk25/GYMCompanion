import '../application/readiness_controller.dart';
import '../domain/readiness_models.dart';

/// A placeholder [ReadinessRepository] — the same disclosed-limitation
/// posture `MockProgressRepository`/`MockFuelRepository` established.
/// Stateful: a submitted check-in must be visible on the very next
/// fetch, so this mock keeps an in-memory `List<ReadinessEntry>`, seeded
/// with two weeks of history (deliberately *not* including today, so
/// the real "Start check-in" flow is immediately reachable rather than
/// already-completed) — reset on every app restart, fully disclosed
/// here rather than silently behaving like a real backend.
///
/// ## `submitCheckIn`'s warnings are illustrative text, never a
/// reimplementation of `ReadinessRuleEngine`
///
/// The real `ReadinessRuleEngine` (backend `domain/readiness/rules/`)
/// evaluates five fixed thresholds — 7h minimum sleep, energy >= 4/10,
/// stress <= 7/10, soreness <= 7/10, resting heart rate <= 70bpm, HRV >=
/// 40ms — and `RecordReadinessHandler` surfaces its recommendations as
/// real `warnings` on `POST /api/v1/readiness`. This mock does **not**
/// duplicate those thresholds — doing so, even disclosed, would be
/// exactly the "recreate backend business logic inside Flutter" this
/// module's own directive forbids, and a client-side copy of a
/// threshold could silently drift from the real one with no way for
/// this codebase to notice. Instead, [submitCheckIn] returns two fixed,
/// clearly-illustrative advisory strings on the very first call only (to
/// demonstrate the real, disclosed UI capability — `ReadinessHomeScreen`
/// really does render whatever `ReadinessCheckInResult.warnings` a
/// repository returns) and an empty list on every call after — never a
/// number comparison against any submitted value, so nothing here could
/// ever be mistaken for a miscalibrated copy of the real rule engine.
class MockReadinessRepository implements ReadinessRepository {
  MockReadinessRepository() : _entries = _seedEntries();

  final List<ReadinessEntry> _entries;
  int _nextId = 100;
  bool _hasShownIllustrativeWarnings = false;

  static List<ReadinessEntry> _seedEntries() {
    final DateTime today = DateTime.now();
    final List<int> sleepHours = <int>[8, 7, 6, 8, 7, 9, 7, 6, 8, 7, 7, 8, 6, 7];
    final List<int> sleepQuality = <int>[7, 6, 5, 8, 6, 8, 7, 5, 7, 6, 6, 7, 5, 6];
    final List<int> energy = <int>[6, 5, 4, 7, 6, 8, 6, 4, 7, 5, 6, 7, 4, 6];
    final List<int> stress = <int>[4, 5, 6, 3, 4, 2, 4, 7, 3, 5, 4, 3, 6, 4];
    final List<int> soreness = <int>[3, 4, 5, 2, 3, 2, 3, 6, 2, 4, 3, 2, 5, 3];
    final List<double> rhr = <double>[54, 56, 58, 53, 55, 51, 54, 59, 52, 56, 55, 53, 58, 54];
    final List<double> hrv = <double>[62, 58, 50, 68, 60, 71, 63, 47, 65, 57, 60, 66, 49, 61];

    return List<ReadinessEntry>.generate(sleepHours.length, (int i) {
      final int daysAgo = sleepHours.length - i; // oldest first while building
      final DateTime date = today.subtract(Duration(days: daysAgo));
      return ReadinessEntry(
        readinessId: 'seed-readiness-$i',
        readinessDate: date,
        recordedAt: date,
        source: ReadinessSource.manual,
        sleepDuration: Duration(hours: sleepHours[i]),
        sleepQuality: sleepQuality[i],
        energyLevel: energy[i],
        stressLevel: stress[i],
        sorenessLevel: soreness[i],
        restingHeartRate: rhr[i],
        heartRateVariability: hrv[i],
      );
    }).reversed.toList(); // newest first
  }

  @override
  Future<ReadinessHomeViewState> fetchHome() async {
    await _delay();
    return ReadinessHomeViewState(
      asOf: DateTime.now(),
      entries: _entries,
      hasCheckedInEver: _entries.isNotEmpty,
    );
  }

  @override
  Future<ReadinessCheckInResult> submitCheckIn({
    required DateTime date,
    Duration? sleepDuration,
    int? sleepQuality,
    int? energyLevel,
    int? stressLevel,
    int? sorenessLevel,
    double? restingHeartRate,
    double? heartRateVariability,
    String? notes,
  }) async {
    await _delay(short: true);
    final ReadinessEntry entry = ReadinessEntry(
      readinessId: 'entry-${_nextId++}',
      readinessDate: date,
      recordedAt: DateTime.now(),
      source: ReadinessSource.manual,
      sleepDuration: sleepDuration,
      sleepQuality: sleepQuality,
      energyLevel: energyLevel,
      stressLevel: stressLevel,
      sorenessLevel: sorenessLevel,
      restingHeartRate: restingHeartRate,
      heartRateVariability: heartRateVariability,
      notes: notes ?? '',
    );
    _entries.insert(0, entry);

    List<String> warnings = const <String>[];
    if (!_hasShownIllustrativeWarnings) {
      _hasShownIllustrativeWarnings = true;
      warnings = const <String>[
        '[warning] Example advisory — real recommendations come from the '
            'backend rule engine once connected.',
        '[warning] This illustrates where check-in advice appears; it is '
            'not computed from the values you just entered.',
      ];
    }
    return ReadinessCheckInResult(entry: entry, warnings: warnings);
  }

  /// See `MockTodayRepository`'s own doc comment for why this delay is
  /// deliberate, not decorative.
  Future<void> _delay({bool short = false}) {
    return Future<void>.delayed(Duration(milliseconds: short ? 80 : 300));
  }
}
