import '../../../core/cache/cache.dart';
import '../../../core/mapping/mapping.dart';
import '../../../core/network/network.dart';
import '../application/today_controller.dart';
import '../domain/today_models.dart';
import 'dto/readiness_summary_dto.dart';
import 'dto/workout_dto.dart';

/// The real [TodayRepository] — the first `ApiXRepository` this project
/// has built (`docs/adr/0046-today-repository-integration.md`), on top
/// of `ApiClient` (`docs/adr/0043`) and the shared mapping convention
/// (`docs/adr/0045`). Wired in `lib/main.dart`, replacing
/// [MockTodayRepository] as [todayRepositoryProvider]'s real
/// implementation; `TodayController`/`TodayScreen` are unchanged — the
/// same "swapping this out is a one-line override" seam
/// [MockTodayRepository]'s own doc comment already described before
/// this class existed.
///
/// ## What's real, and what's a disclosed gap
///
/// `Workout` (`backend/app/domain/workout/workout.py`) and readiness
/// check-in *dates* (`backend/app/domain/readiness/`) are real,
/// authenticated backend data — [hasActivePlan], [sessionStatus],
/// [TodaySessionSummary]'s own fields, and [checkInCompletedToday] all
/// come from one real GET each.
///
/// [readinessBand] is always [ReadinessBand.normal] here — not derived,
/// not computed client-side. `docs/adr/0039-progress-module.md` already
/// found the composite readiness score `ReadinessRuleEngine` computes
/// is never returned by any endpoint; this repository confirms the same
/// gap applies to Today. Computing a band from the raw sleep/energy/
/// stress/soreness/HRV fields client-side would mean re-implementing
/// `ReadinessRuleEngine`'s own scoring logic in Flutter — exactly what
/// this phase's "never duplicate backend business logic" rule forbids.
/// See `docs/TECH_DEBT.md`'s TD-0006.
///
/// [streak] and [task] are always `null` — the backend has no Habit/
/// Streak or Task/Recommendation persistence at all (confirmed by a
/// full domain/application package sweep finding no such aggregate
/// exists anywhere in `backend/app/`). `TodayViewState.streak`/`.task`
/// are already nullable, so this is a real, honest absence, not a
/// fabricated one — `TodayScreen` already renders correctly with either
/// `null` (see `_TodayContent`'s existing `if (state.task != null)`/
/// `if (state.streak != null)` guards). See TD-0006.
///
/// [TodayViewState.isOffline] reflects a real read-through cache as of
/// Step 4 (`docs/adr/0052-offline-caching.md`): [fetchToday] serves a
/// fresh-enough cached bundle immediately (revalidating in the
/// background), falls back to the last cached bundle on a genuine
/// network failure, and otherwise fetches live and writes through —
/// see `core/cache/read_through_cache.dart`'s own doc comment for the
/// full shared policy every real repository's own `fetchHome()` now
/// reuses unchanged.
class ApiTodayRepository implements TodayRepository {
  ApiTodayRepository(this._client, this._cache);

  final ApiClient _client;
  final LocalCache _cache;

  static const String _cacheKey = 'today';

  @override
  Future<TodayViewState> fetchToday() {
    return readThroughCache<TodayViewState>(
      cache: _cache,
      key: _cacheKey,
      maxAge: kCacheFreshDuration,
      fetchRawJson: _fetchRawJson,
      build: _buildViewState,
    );
  }

  /// The real network half of [fetchToday] — exactly the two `GET`s this
  /// method always made, now returning their raw decoded JSON bundled
  /// into one cacheable `Map` rather than being parsed immediately, so
  /// [_buildViewState] can run identically over a live or a cached
  /// bundle.
  Future<Object?> _fetchRawJson() async {
    final List<List<dynamic>> results = await Future.wait(<Future<List<dynamic>>>[
      _client.getList('${ApiConfig.v1PathPrefix}/workouts'),
      _client.getList('${ApiConfig.v1PathPrefix}/readiness'),
    ]);
    return <String, dynamic>{'workouts': results[0], 'readiness': results[1]};
  }

  /// The real parsing/derivation logic [fetchToday] always ran —
  /// unchanged, just factored out so it can run over either a fresh or
  /// a cached [rawJson] bundle, per [readThroughCache]'s own contract.
  TodayViewState _buildViewState(Object? rawJson, {required bool isOffline}) {
    final Map<String, dynamic> bundle = rawJson! as Map<String, dynamic>;
    final List<WorkoutDto> workouts = (bundle['workouts']! as List<dynamic>)
        .cast<Map<String, dynamic>>()
        .map(WorkoutDto.fromJson)
        .toList(growable: false);
    final List<ReadinessSummaryDto> readinessEntries = (bundle['readiness']! as List<dynamic>)
        .cast<Map<String, dynamic>>()
        .map(ReadinessSummaryDto.fromJson)
        .toList(growable: false);

    final DateTime today = DateTime.now();
    final String todayKey = apiDateString(today);

    // "Has an Active Plan" — the closest honest translation of the UX/UI
    // Design Bible's own phrase onto what `Workout` actually models: at
    // least one workout exists that hasn't been cancelled. Not "a
    // workout exists for today specifically" — a user with a plan whose
    // next session is tomorrow still has an Active Plan.
    final bool hasActivePlan = workouts.any((WorkoutDto w) => w.status != 'cancelled');

    final WorkoutDto? todaysWorkout = _findTodaysWorkout(workouts, todayKey);
    final SessionCardStatus sessionStatus = _sessionStatusFor(todaysWorkout);
    final TodaySessionSummary? session = todaysWorkout == null
        ? null
        : TodaySessionSummary(
            workoutId: todaysWorkout.workoutId,
            name: todaysWorkout.name,
            plannedDate: todaysWorkout.plannedDate,
            goal: todaysWorkout.goal,
            notes: todaysWorkout.notes,
          );

    final bool checkInCompletedToday = readinessEntries.any(
      (ReadinessSummaryDto r) => apiDateString(r.readinessDate) == todayKey,
    );

    return TodayViewState(
      date: today,
      hasActivePlan: hasActivePlan,
      readinessBand: ReadinessBand.normal,
      checkInCompletedToday: checkInCompletedToday,
      sessionStatus: sessionStatus,
      session: session,
      isOffline: isOffline,
    );
  }

  /// A cancelled workout planned for today is treated the same as no
  /// workout at all (falls through to [SessionCardStatus.empty]) — from
  /// the user's perspective there is nothing to do today either way,
  /// and `TodaySessionSummary` has no field to represent "cancelled"
  /// distinctly from "absent" (the mock this replaces never modeled a
  /// cancelled state either).
  WorkoutDto? _findTodaysWorkout(List<WorkoutDto> workouts, String todayKey) {
    for (final WorkoutDto workout in workouts) {
      if (workout.status != 'cancelled' && apiDateString(workout.plannedDate) == todayKey) {
        return workout;
      }
    }
    return null;
  }

  /// `planned`/`in_progress` both read as "ready to start or resume" —
  /// `SessionCardStatus` has no separate "in progress" rendering of its
  /// own (see `session_card.dart`'s own five-state switch), so both
  /// backend statuses map onto the one [SessionCardStatus.ready] state
  /// that already covers "there's a session to start" today.
  SessionCardStatus _sessionStatusFor(WorkoutDto? workout) {
    if (workout == null) {
      return SessionCardStatus.empty;
    }
    return workout.status == 'completed' ? SessionCardStatus.completed : SessionCardStatus.ready;
  }
}
