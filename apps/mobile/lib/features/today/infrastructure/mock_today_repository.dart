import '../application/today_controller.dart';
import '../domain/today_models.dart';

/// A placeholder [TodayRepository], returning a fixed, realistic snapshot
/// instead of a real network call.
///
/// **This is temporary and is disclosed as such deliberately** — the same
/// posture ADR 0002 already established for Flutter verification in this
/// sandbox, applied here to a missing data layer instead of a missing
/// SDK. The backend already exposes real readiness, workout, and habit/
/// streak data (`backend/app/api/routes/v1/`); wiring an authenticated
/// HTTP client, response mapping onto `TodayViewState`, and local
/// caching for the offline state are later, separately-scoped
/// implementation stages, not something one screen's build should absorb
/// speculatively. Swapping this out is a one-line change: override
/// [todayRepositoryProvider] with the real implementation wherever it is
/// built; nothing in `TodayScreen` or `TodayController` changes.
class MockTodayRepository implements TodayRepository {
  const MockTodayRepository();

  @override
  Future<TodayViewState> fetchToday() async {
    // The delay is deliberate, not decorative: it lets `TodayScreen`'s
    // skeleton-loading state actually be observed during development
    // (and in a widget test's first `pump()`) instead of always
    // resolving synchronously, which would silently hide a bug in the
    // loading branch. `flutter_test`'s fake async clock resolves this
    // instantly in tests either way.
    await Future<void>.delayed(const Duration(milliseconds: 300));

    return TodayViewState(
      date: DateTime.now(),
      hasActivePlan: true,
      readinessBand: ReadinessBand.normal,
      checkInCompletedToday: false,
      sessionStatus: SessionCardStatus.ready,
      session: const TodaySessionSummary(
        tier: SessionTier.standard,
        durationEstimateMinutes: 45,
        keyLifts: <String>['Back Squat', 'Bench Press', 'Barbell Row'],
        oneLineSummary: 'A standard session fits today — nothing flagged.',
      ),
      streak: const TodayStreak(currentDays: 12, graceUsed: false),
      task: const TodayTask(
        text: 'Your bench press has stalled for three sessions.',
        actionLabel: 'Review',
        rationale: 'Based on your last 3 logged sessions at this weight.',
      ),
    );
  }
}
