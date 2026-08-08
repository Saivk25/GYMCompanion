import '../../../core/mapping/mapping.dart';
import '../../../core/network/network.dart';
import '../../../shared/domain/session_tier.dart';
import '../application/train_controller.dart';
import '../domain/train_models.dart';
import 'dto/train_session_dto.dart';
import 'dto/train_workout_dto.dart';

/// The real [TrainRepository] — the third `ApiXRepository` this project
/// has built (`docs/adr/0048-train-repository-integration.md`), on the
/// same `ApiClient` (`docs/adr/0043`) and shared mapping convention
/// (`docs/adr/0045`) `ApiTodayRepository`/`ApiReadinessRepository` already
/// proved. Wired in `lib/main.dart`, replacing [MockTrainRepository];
/// every Train screen and controller is unchanged.
///
/// ## What's real
///
/// [fetchHome]/[fetchWorkout] → `GET /api/v1/workouts` /
/// `GET /api/v1/workouts/{id}`. [startSession] → `POST /api/v1/workouts/
/// {id}/sessions`, then a real refetch (`GET /api/v1/workout-sessions/
/// {id}`) per this phase's "mutate → refetch" instruction — the backend
/// only ever returns `IdResponse{id, warnings}` from a mutation
/// (`backend/app/api/schemas/common.py`), never the created/updated
/// resource itself. [fetchSession] → `GET /api/v1/workout-sessions/{id}`.
/// [completeSession] → `POST /api/v1/workout-sessions/{id}/complete`,
/// also mutate → refetch. `CoachSignalLog`'s push of
/// `completeSession`'s real warnings happens unchanged at the controller
/// level (`ActiveSessionController.completeSession`,
/// `application/train_controller.dart`) — this repository only supplies
/// the real strings via [TrainSession.lastMutationWarnings].
///
/// ## Three disclosed, deliberate gaps — not defaults, not silent
/// omissions
///
/// 1. **`workoutName` denormalization.** `WorkoutSessionResponse` carries
///    only `workout_id`. [_fetchFullSession] resolves the real name with
///    a second `GET /api/v1/workouts/{workout_id}` rather than inventing
///    one — an extra round trip, not a shortcut.
/// 2. **`tier` is accepted by [startSession]'s signature (interface
///    compatibility with [TrainRepository]) but never transmitted.**
///    `StartWorkoutSessionRequest` (`backend/app/api/schemas/
///    workout.py`) has exactly one field, `session_date` — no tier
///    concept exists anywhere in the backend. See `docs/TECH_DEBT.md`
///    TD-0007 and `pre_session_screen.dart`'s own doc comment: the
///    `TierPicker` UI is kept as a disclosed, inert, client-side-only
///    control, not removed and not silently wired to nothing.
/// 3. **[logSet]/[completeSet] always throw
///    [TrainLoggingUnavailableException], synchronously, before any
///    network call.** No `GET /exercises`-shaped endpoint exists
///    anywhere in this backend to discover a real `exercise_id`
///    (confirmed: `grep -rli "exercise" backend/app/api` finds no
///    `exercise.py` route file at all), and `LogExerciseSetHandler`
///    (`backend/app/application/workout/handlers/
///    log_exercise_set_handler.py`) 404s on any id the real seeded
///    Exercise table doesn't already recognize — there is no id this
///    client could honestly send. This was surfaced and the deferral
///    explicitly approved rather than decided unilaterally; see
///    `docs/adr/0048` for the full record.
///
/// [TrainHomeViewState.history] is always `[]` — also explicitly
/// approved, not a default filled in silently: no
/// `GET /workout-sessions` (list) endpoint exists on this backend at
/// all (confirmed by reading `backend/app/api/routes/v1/workout.py` in
/// full — ten endpoints, none of them a session list), so there is no
/// real data to populate it from. `TrainHomeScreen`'s existing
/// `AppEmptyState` for an empty history list already renders correctly;
/// no presentation change was made or needed.
///
/// [TrainHomeViewState.thisWeek] is a client-side filter over the full,
/// unfiltered `GET /api/v1/workouts` response (no non-cancelled,
/// non-completed workout planned more than 6 days from today) — the
/// backend supports no date-range query parameter at all (ADR 0042 Part
/// 2's own "no pagination or filtering exists anywhere" finding, reused
/// here rather than treated as a new gap). This is a real, disclosed
/// heuristic over real data, not a fabricated field.
class ApiTrainRepository implements TrainRepository {
  ApiTrainRepository(this._client);

  final ApiClient _client;

  @override
  Future<TrainHomeViewState> fetchHome() async {
    final List<dynamic> raw = await _client.getList('${ApiConfig.v1PathPrefix}/workouts');
    final List<TrainWorkout> workouts = raw
        .cast<Map<String, dynamic>>()
        .map(TrainWorkoutDto.fromJson)
        .map((TrainWorkoutDto dto) => dto.toDomain())
        .toList(growable: false);

    final bool hasActivePlan = workouts.any((TrainWorkout w) => w.status != WorkoutStatus.cancelled);

    final DateTime today = DateTime.now();
    final DateTime weekCutoff =
        DateTime(today.year, today.month, today.day).add(const Duration(days: 6));
    final List<TrainWorkout> thisWeek = workouts
        .where(
          (TrainWorkout w) =>
              (w.status == WorkoutStatus.planned || w.status == WorkoutStatus.inProgress) &&
              !w.plannedDate.isAfter(weekCutoff),
        )
        .toList()
      ..sort((TrainWorkout a, TrainWorkout b) => a.plannedDate.compareTo(b.plannedDate));

    return TrainHomeViewState(
      status: TrainHomeStatus.ready,
      hasActivePlan: hasActivePlan,
      thisWeek: thisWeek,
      // No `GET /workout-sessions` list endpoint exists — see this
      // class's own doc comment.
      history: const <TrainSession>[],
      isOffline: false,
    );
  }

  @override
  Future<TrainWorkout> fetchWorkout(String workoutId) async {
    final Map<String, dynamic> json =
        await _client.get('${ApiConfig.v1PathPrefix}/workouts/$workoutId');
    return TrainWorkoutDto.fromJson(json).toDomain();
  }

  @override
  Future<TrainSession> startSession(String workoutId, {required SessionTier tier}) async {
    // `tier` is intentionally unused — see this class's own doc comment,
    // gap 2.
    final Map<String, dynamic> result = await _client.post(
      '${ApiConfig.v1PathPrefix}/workouts/$workoutId/sessions',
      body: <String, dynamic>{'session_date': apiDateString(DateTime.now())},
    );
    final String sessionId = result.requireString('id');
    final List<String> warnings =
        (result.optionalList('warnings') ?? const <dynamic>[]).cast<String>();
    return _fetchFullSession(sessionId, warnings: warnings);
  }

  @override
  Future<TrainSession> fetchSession(String sessionId) => _fetchFullSession(sessionId);

  @override
  Future<TrainSession> logSet(
    String sessionId, {
    required String exerciseId,
    required String exerciseName,
    required int setNumber,
    required double weight,
    required int reps,
    required int rpe,
  }) async {
    throw const TrainLoggingUnavailableException(
      'Set logging needs a backend exercise catalog that does not exist '
      'yet — see docs/adr/0048-train-repository-integration.md.',
    );
  }

  @override
  Future<TrainSession> completeSet(
    String sessionId, {
    required String performanceId,
    required int setNumber,
  }) async {
    throw const TrainLoggingUnavailableException(
      'Set logging needs a backend exercise catalog that does not exist '
      'yet — see docs/adr/0048-train-repository-integration.md.',
    );
  }

  @override
  Future<TrainSession> completeSession(
    String sessionId, {
    required double durationSeconds,
    required double completionPercentage,
    int? rating,
  }) async {
    final Map<String, dynamic> result = await _client.post(
      '${ApiConfig.v1PathPrefix}/workout-sessions/$sessionId/complete',
      body: <String, dynamic>{
        'duration_seconds': durationSeconds,
        'completion_percentage': completionPercentage,
        if (rating != null) 'rating': rating,
      },
    );
    final List<String> warnings =
        (result.optionalList('warnings') ?? const <dynamic>[]).cast<String>();
    return _fetchFullSession(sessionId, warnings: warnings);
  }

  /// The one "mutate → refetch" helper every mutation in this repository
  /// routes through — a real `GET /api/v1/workout-sessions/{id}` for the
  /// authoritative session, then a real `GET /api/v1/workouts/{workout_id}`
  /// to resolve [TrainSession.workoutName] (see this class's own doc
  /// comment, gap 1). [warnings] is only ever non-empty right after a
  /// mutation; a plain [fetchSession] passes none, matching
  /// `ReadinessHomeController`'s own "transient, not persisted, genuinely
  /// empty after the next fetch" reasoning for the equivalent field there.
  Future<TrainSession> _fetchFullSession(String sessionId, {List<String> warnings = const <String>[]}) async {
    final Map<String, dynamic> sessionJson =
        await _client.get('${ApiConfig.v1PathPrefix}/workout-sessions/$sessionId');
    final TrainSessionDto sessionDto = TrainSessionDto.fromJson(sessionJson);

    final Map<String, dynamic> workoutJson =
        await _client.get('${ApiConfig.v1PathPrefix}/workouts/${sessionDto.workoutId}');
    final TrainWorkoutDto workoutDto = TrainWorkoutDto.fromJson(workoutJson);

    return sessionDto.toDomain(workoutName: workoutDto.name, lastMutationWarnings: warnings);
  }
}
