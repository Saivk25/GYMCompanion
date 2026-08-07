/// Pure Dart value types for the Train module — no Flutter import anywhere
/// in this file, matching `features/today/domain/today_models.dart`'s own
/// rule. Naming mirrors `backend/app/api/schemas/workout.py`'s response
/// shapes field-for-field (`WorkoutResponse`, `WorkoutSessionResponse`,
/// `ExercisePerformanceResponse`, `ExerciseSetResponse`) and the two
/// backend status enums (`app/domain/workout/enums.py`'s `WorkoutStatus`,
/// `app/domain/workout_session/enums.py`'s `SessionStatus`) so a future
/// real `TrainRepository` mapping API responses onto these types is a
/// direct translation, not a re-interpretation — the same discipline
/// ADR 0036 established for Today.
///
/// ## One denormalized field, disclosed here rather than hidden
///
/// `ExercisePerformanceResponse` carries only `exercise_id`, never a
/// display name — there is no backend endpoint today that resolves an
/// exercise id to a human-readable name (`backend/app/api/routes/v1/`
/// has no `exercise.py` route file at all). [TrainExercisePerformance]
/// still needs one to render anything, so `exerciseName` is a real field
/// here — but it is documented at its declaration, not silently assumed,
/// and a real repository inherits the same open question this comment
/// names rather than the domain layer quietly hiding it.
library;

import '../../../shared/domain/session_tier.dart';

/// The Workout aggregate's lifecycle (`app/domain/workout/enums.py`,
/// verbatim values `planned`/`in_progress`/`completed`/`cancelled`).
enum WorkoutStatus { planned, inProgress, completed, cancelled }

/// The WorkoutSession aggregate's lifecycle (`app/domain/workout_session/
/// enums.py`, verbatim values `planned`/`active`/`completed`/`abandoned`)
/// — deliberately a distinct type from [WorkoutStatus], not reused, for
/// the same reason the backend keeps them distinct (see that file's own
/// doc comment: a planned intention vs. its execution record).
enum SessionStatus { planned, active, completed, abandoned }

/// A single logged set (`ExerciseSetResponse`: `set_number`, `weight`,
/// `reps`, `rpe`, `completed`). Logging is genuinely two backend calls
/// (`LogExerciseSetRequest` creates the entry; a separate
/// `CompleteExerciseSetRequest` marks it done by `set_number`) — this
/// type carries [completed] as its own field rather than inferring it,
/// so the Active Workout screen can show a set that has been logged but
/// not yet confirmed, matching the real two-step backend flow.
class TrainExerciseSet {
  const TrainExerciseSet({
    required this.setNumber,
    required this.weight,
    required this.reps,
    required this.rpe,
    required this.completed,
  });

  final int setNumber;
  final double weight;
  final int reps;
  final int rpe;
  final bool completed;

  TrainExerciseSet copyWith({
    double? weight,
    int? reps,
    int? rpe,
    bool? completed,
  }) {
    return TrainExerciseSet(
      setNumber: setNumber,
      weight: weight ?? this.weight,
      reps: reps ?? this.reps,
      rpe: rpe ?? this.rpe,
      completed: completed ?? this.completed,
    );
  }
}

/// One exercise's performance within a session
/// (`ExercisePerformanceResponse`: `performance_id`, `exercise_id`,
/// `notes`, `sets`). See this file's own top comment for why
/// [exerciseName] exists here despite having no backend counterpart yet.
class TrainExercisePerformance {
  const TrainExercisePerformance({
    required this.performanceId,
    required this.exerciseId,
    required this.exerciseName,
    required this.sets,
    this.notes = '',
    this.targetSets,
    this.targetReps,
    this.targetWeight,
  });

  final String performanceId;
  final String exerciseId;
  final String exerciseName;
  final List<TrainExerciseSet> sets;
  final String notes;

  /// The progression engine's suggested target for this exercise today
  /// (UX/UI Design Bible Section 5.2: "target from the progression
  /// engine"). `null` when no target is available — the logging row
  /// still works without one, it just has nothing to compare against.
  final int? targetSets;
  final int? targetReps;
  final double? targetWeight;

  bool get isComplete => sets.isNotEmpty && sets.every((s) => s.completed);
}

/// A planned workout (`WorkoutResponse`). `plannedExerciseNames` is a
/// glance-length preview, not a real backend field — the Workout
/// aggregate itself has no exercise list (`app/domain/workout/workout.py`
/// confirms no such field); a workout's actual exercises only come into
/// existence as [TrainExercisePerformance] entries once a session starts
/// logging them. This mirrors exactly how Today's own `keyLifts` preview
/// already works (`today_models.dart`) — a short mock preview inside the
/// same disclosed mock repository, not a claim of real backend data.
class TrainWorkout {
  const TrainWorkout({
    required this.workoutId,
    required this.name,
    required this.plannedDate,
    required this.status,
    this.goal,
    this.notes,
    this.durationSeconds,
    this.startedAt,
    this.completedAt,
    this.plannedExerciseNames = const <String>[],
    this.tier = SessionTier.standard,
    this.estimatedMinutes = 45,
  });

  final String workoutId;
  final String name;
  final DateTime plannedDate;
  final WorkoutStatus status;
  final String? goal;
  final String? notes;
  final double? durationSeconds;
  final DateTime? startedAt;
  final DateTime? completedAt;
  final List<String> plannedExerciseNames;
  final SessionTier tier;
  final int estimatedMinutes;
}

/// A workout session — the execution record (`WorkoutSessionResponse`).
/// `workoutName` is denormalized here for the same reason
/// `TrainExercisePerformance.exerciseName` is: `WorkoutSessionResponse`
/// carries only `workout_id`, and resolving it to a name would need a
/// join a real repository is responsible for, not this domain layer.
class TrainSession {
  const TrainSession({
    required this.sessionId,
    required this.workoutId,
    required this.workoutName,
    required this.status,
    required this.sessionDate,
    required this.exercisePerformances,
    this.notes = '',
    this.durationSeconds,
    this.completionPercentage,
    this.rating,
    this.startedAt,
    this.completedAt,
    this.abandonedAt,
    this.lastMutationWarnings = const <String>[],
  });

  final String sessionId;
  final String workoutId;
  final String workoutName;
  final SessionStatus status;
  final DateTime sessionDate;
  final List<TrainExercisePerformance> exercisePerformances;
  final String notes;
  final double? durationSeconds;
  final double? completionPercentage;
  final int? rating;
  final DateTime? startedAt;
  final DateTime? completedAt;
  final DateTime? abandonedAt;

  /// The real advisory strings the *most recent* mutation on this
  /// session returned — `POST .../complete` surfaces
  /// `ProgressiveOverloadRuleEngine` + `TrainingLoadRuleEngine` advice
  /// this way (`docs/adr/0041-coach-module.md`); `POST .../sets` surfaces
  /// `ExerciseRecommendationRuleEngine` advice the same way, though that
  /// engine's real handler only ever supplies it a minimal context
  /// (see that ADR's research section), so it realistically produces
  /// little. Transient like `ReadinessHomeViewState
  /// .lastCheckInWarnings` — not persisted, not re-derivable from a
  /// plain fetch, genuinely empty again after the next `fetchSession`.
  /// Defaults to `()` so every other call site constructing a
  /// [TrainSession] (seed data, `copyWith`-shaped rebuilds elsewhere in
  /// the mock) is unaffected by this field's addition.
  final List<String> lastMutationWarnings;
}

/// Train Home's sub-state for its own content region — independent of
/// the page-level fetch lifecycle, mirroring [SessionCardStatus]'s own
/// reasoning in `today_models.dart`: a plan-generation hiccup here should
/// not blank the whole tab.
enum TrainHomeStatus { loading, ready, empty, error }

/// The complete state Train Home renders from once its initial fetch has
/// resolved. `thisWeek`/`history` back the Bible's "This Week / History"
/// in-page tabs (Section 4); Library has no state here at all — it is a
/// permanently disclosed placeholder (see `ExerciseLibraryPlaceholder`),
/// not fetched data, because no backend exercise-catalog endpoint exists
/// to fetch from.
class TrainHomeViewState {
  const TrainHomeViewState({
    required this.status,
    this.hasActivePlan = true,
    this.thisWeek = const <TrainWorkout>[],
    this.history = const <TrainSession>[],
    this.isOffline = false,
  });

  final TrainHomeStatus status;
  final bool hasActivePlan;
  final List<TrainWorkout> thisWeek;
  final List<TrainSession> history;
  final bool isOffline;
}

/// A personal record — modeled for a future real repository even though
/// no backend endpoint exists to serve it from today (see
/// `PersonalRecordsScreen`'s own doc comment).
class TrainPersonalRecord {
  const TrainPersonalRecord({
    required this.exerciseName,
    required this.value,
    required this.achievedOn,
  });

  final String exerciseName;
  final String value;
  final DateTime achievedOn;
}
