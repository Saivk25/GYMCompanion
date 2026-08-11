import '../application/today_controller.dart';
import '../domain/today_models.dart';

/// A test/development-only [TodayRepository] fixture — no longer the
/// production implementation as of `docs/adr/0046-today-repository-
/// integration.md` (`ApiTodayRepository`,
/// `../infrastructure/api_today_repository.dart`, is; wired in
/// `lib/main.dart`). Kept for `test/features/today/today_screen_test.dart`
/// and any future widget test that wants a deterministic, zero-network
/// fixture rather than an `ApiClient` fake.
///
/// This fixture's `streak`/`task` values are illustrative only —
/// `ApiTodayRepository` always returns `null` for both, since the
/// backend has no Habit/Streak or Task/Recommendation persistence at
/// all (see that repository's own doc comment). `session.goal`/`.notes`
/// here are similarly illustrative — a real `Workout`'s `goal`/`notes`
/// are free text a user or plan entered, not guaranteed to look like
/// this.
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
      session: TodaySessionSummary(
        // Matches `MockTrainRepository`'s own fixture id for today's
        // workout, so a mock-based tap-through from Today's "Start
        // session" into Train's Pre-session screen still resolves.
        workoutId: 'workout-today',
        name: 'Upper Body Strength',
        plannedDate: DateTime.now(),
        goal: 'Build strength',
        notes: 'Back Squat · Bench Press · Barbell Row',
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
