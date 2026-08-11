import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/application/coach_signal_log.dart';
import '../../../shared/domain/coach_signal.dart';
import '../../../shared/domain/session_tier.dart';
import '../domain/train_models.dart';

/// The seam between Train's presentation layer and wherever its data
/// actually comes from — mirrors `TodayRepository`'s own role and
/// reasoning (`features/today/application/today_controller.dart`)
/// exactly: an abstract interface, never a concrete HTTP client, so the
/// eventual real implementation is a provider override, not a rewrite.
///
/// Every method here corresponds to a real backend endpoint that already
/// exists (`backend/app/api/routes/v1/workout.py`) — [fetchHome] reads
/// from `GET /workouts`, [startSession] from `POST /workouts/{id}/
/// sessions`, [fetchSession] from `GET /workout-sessions/{id}`, [logSet]
/// from `POST /workout-sessions/{id}/sets`, [completeSet] from
/// `POST /workout-sessions/{id}/sets/complete`, [completeSession] from
/// `POST /workout-sessions/{id}/complete`. There is deliberately no
/// method here for personal records or an exercise catalog — no backend
/// endpoint exists for either today, so `PersonalRecordsScreen` and
/// `ExerciseDetailScreen` render a disclosed "not connected yet" state
/// directly rather than calling a repository method that could only ever
/// return nothing. See `docs/adr/0037-train-module.md` for the full
/// reasoning behind this split.
/// Thrown by [TrainRepository.logSet]/[TrainRepository.completeSet] when
/// the call cannot be serviced at all — see `docs/adr/0048-train-
/// repository-integration.md`: no `GET /exercises`-shaped endpoint
/// exists anywhere in the backend to discover a real `exercise_id`, and
/// `LogExerciseSetHandler` (`backend/app/application/workout/handlers/
/// log_exercise_set_handler.py`) 404s on any id the real seeded Exercise
/// table doesn't already recognize. `ApiTrainRepository` throws this
/// synchronously, before attempting any network call, rather than
/// sending a request that could only ever fail — a deliberate,
/// user-approved deferral (Train's exercise-catalog gap), not a bug.
/// [MockTrainRepository] never throws it. `ActiveWorkoutScreen` catches
/// it specifically to show permanent-unavailability copy instead of
/// generic "try again" phrasing that would mislead the user into
/// retrying something that can never succeed.
class TrainLoggingUnavailableException implements Exception {
  const TrainLoggingUnavailableException(this.message);

  final String message;

  @override
  String toString() => message;
}

abstract interface class TrainRepository {
  Future<TrainHomeViewState> fetchHome();

  Future<TrainWorkout> fetchWorkout(String workoutId);

  Future<TrainSession> startSession(String workoutId, {required SessionTier tier});

  Future<TrainSession> fetchSession(String sessionId);

  Future<TrainSession> logSet(
    String sessionId, {
    required String exerciseId,
    required String exerciseName,
    required int setNumber,
    required double weight,
    required int reps,
    required int rpe,
  });

  Future<TrainSession> completeSet(
    String sessionId, {
    required String performanceId,
    required int setNumber,
  });

  Future<TrainSession> completeSession(
    String sessionId, {
    required double durationSeconds,
    required double completionPercentage,
    int? rating,
  });
}

/// No default implementation — the same "throw until overridden" posture
/// [todayRepositoryProvider] uses, so a missing override fails loudly in
/// `main.dart` or a test rather than silently rendering an error state.
final Provider<TrainRepository> trainRepositoryProvider =
    Provider<TrainRepository>((ref) => throw UnimplementedError(
          'trainRepositoryProvider has no default implementation — see '
          'lib/main.dart, which overrides it with MockTrainRepository '
          'until a real API-backed repository exists.',
        ),
    );

/// Train Home's page-level fetch lifecycle — thin, like `TodayController`:
/// its only job is calling [TrainRepository.fetchHome] and re-exposing the
/// result plus a [refresh] for pull-to-refresh and retry.
class TrainHomeController extends AsyncNotifier<TrainHomeViewState> {
  @override
  Future<TrainHomeViewState> build() {
    return ref.read(trainRepositoryProvider).fetchHome();
  }

  Future<void> refresh() async {
    state = const AsyncValue<TrainHomeViewState>.loading();
    state = await AsyncValue.guard(
      () => ref.read(trainRepositoryProvider).fetchHome(),
    );
  }
}

final AsyncNotifierProvider<TrainHomeController, TrainHomeViewState>
    trainHomeControllerProvider =
    AsyncNotifierProvider<TrainHomeController, TrainHomeViewState>(
  TrainHomeController.new,
);

/// One workout's Pre-session data, keyed by `workoutId` — a family
/// provider because more than one workout can be previewed across a
/// session's navigation history (Today's session card links to today's
/// workout; Train Home's "This Week" list links to others).
class PreSessionController extends FamilyAsyncNotifier<TrainWorkout, String> {
  @override
  Future<TrainWorkout> build(String workoutId) {
    return ref.read(trainRepositoryProvider).fetchWorkout(workoutId);
  }

  Future<void> refresh(String workoutId) async {
    state = const AsyncValue<TrainWorkout>.loading();
    state = await AsyncValue.guard(
      () => ref.read(trainRepositoryProvider).fetchWorkout(workoutId),
    );
  }

  /// Starts a session for the previewed workout at the chosen [tier] and
  /// returns the new session's id, for the screen to navigate with. Lives
  /// on this controller — not called directly from `PreSessionScreen` —
  /// so the mutation stays behind the same Repository/Provider seam every
  /// other write in this module goes through (this project's own "no
  /// shortcuts" architecture rule).
  Future<String> startSession(SessionTier tier) async {
    final TrainSession session = await ref
        .read(trainRepositoryProvider)
        .startSession(arg, tier: tier);
    return session.sessionId;
  }
}

final AsyncNotifierProviderFamily<PreSessionController, TrainWorkout, String>
    preSessionControllerProvider =
    AsyncNotifierProvider.family<PreSessionController, TrainWorkout, String>(
  PreSessionController.new,
);

/// An in-progress (or just-completed, or past) session, keyed by
/// `sessionId`. Unlike Today's read-only controller, this one is also
/// the single place every logging mutation goes through
/// (`logSet`/`completeSet`/`completeSession`) — the Active Workout screen
/// never mutates a [TrainSession] locally and hopes the next fetch agrees
/// with it; every mutation round-trips through [TrainRepository] and the
/// *returned* session becomes the new state, so the screen always renders
/// exactly what the repository (eventually: the backend) considers true.
/// This matters specifically for offline logging (UX/UI Design Bible,
/// Section 5.2: "Logging works locally, syncs when reconnected") — a
/// future real repository can queue-and-optimistically-return here
/// without this controller or the screen needing to change at all.
class ActiveSessionController extends FamilyAsyncNotifier<TrainSession, String> {
  @override
  Future<TrainSession> build(String sessionId) {
    return ref.read(trainRepositoryProvider).fetchSession(sessionId);
  }

  // `logSet`/`completeSet`/`completeSession` deliberately do *not* use
  // `AsyncValue.guard` the way `TrainHomeController.refresh` does. A
  // guarded failure here would turn `state` into `AsyncValue.error`,
  // which `ActiveWorkoutScreen`'s top-level `state.when(...)` would
  // render as a full-page error — exactly the "blocking error screen"
  // this app's own design philosophy rejects, and far too heavy a
  // response to one failed set log in the middle of an otherwise-fine
  // session. Instead these rethrow on failure with `state` left
  // untouched (the screen keeps showing the last-known-good session),
  // and `ActiveWorkoutScreen` catches the exception locally to show a
  // narrow, scoped `SnackBar` — the same card-scoped-error precedent
  // `SessionCard`'s own error state established for Today.
  Future<void> logSet({
    required String exerciseId,
    required String exerciseName,
    required int setNumber,
    required double weight,
    required int reps,
    required int rpe,
  }) async {
    final String sessionId = arg;
    final TrainSession updated = await ref.read(trainRepositoryProvider).logSet(
          sessionId,
          exerciseId: exerciseId,
          exerciseName: exerciseName,
          setNumber: setNumber,
          weight: weight,
          reps: reps,
          rpe: rpe,
        );
    state = AsyncValue<TrainSession>.data(updated);
  }

  Future<void> completeSet({
    required String performanceId,
    required int setNumber,
  }) async {
    final String sessionId = arg;
    final TrainSession updated = await ref.read(trainRepositoryProvider).completeSet(
          sessionId,
          performanceId: performanceId,
          setNumber: setNumber,
        );
    state = AsyncValue<TrainSession>.data(updated);
  }

  Future<void> completeSession({
    required double durationSeconds,
    required double completionPercentage,
    int? rating,
  }) async {
    final String sessionId = arg;
    final TrainSession updated = await ref.read(trainRepositoryProvider).completeSession(
          sessionId,
          durationSeconds: durationSeconds,
          completionPercentage: completionPercentage,
          rating: rating,
        );
    // Coach's one real cross-module data source (`docs/adr/0041-coach-
    // module.md`) — the same real strings `ProgressiveOverloadRuleEngine`/
    // `TrainingLoadRuleEngine` produced, tagged `CoachModule.training`,
    // never recomputed here.
    ref.read(coachSignalLogProvider.notifier).add(
          CoachModule.training,
          updated.lastMutationWarnings,
        );
    state = AsyncValue<TrainSession>.data(updated);
  }
}

final AsyncNotifierProviderFamily<ActiveSessionController, TrainSession, String>
    activeSessionControllerProvider = AsyncNotifierProvider.family<
        ActiveSessionController, TrainSession, String>(
  ActiveSessionController.new,
);
