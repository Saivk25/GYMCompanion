import '../../../../core/mapping/mapping.dart';
import '../../domain/train_models.dart';

/// Mirrors `ExerciseSetResponse` exactly (`backend/app/api/schemas/
/// workout.py`) — `set_number, weight, reps, rpe, completed`, all
/// required, none optional on the wire.
class ExerciseSetDto {
  const ExerciseSetDto({
    required this.setNumber,
    required this.weight,
    required this.reps,
    required this.rpe,
    required this.completed,
  });

  factory ExerciseSetDto.fromJson(Map<String, dynamic> json) {
    return ExerciseSetDto(
      setNumber: json.requireInt('set_number'),
      weight: json.requireDouble('weight'),
      reps: json.requireInt('reps'),
      rpe: json.requireInt('rpe'),
      completed: json.requireBool('completed'),
    );
  }

  final int setNumber;
  final double weight;
  final int reps;
  final int rpe;
  final bool completed;

  TrainExerciseSet toDomain() {
    return TrainExerciseSet(
      setNumber: setNumber,
      weight: weight,
      reps: reps,
      rpe: rpe,
      completed: completed,
    );
  }
}

/// Mirrors `ExercisePerformanceResponse` exactly (`performance_id,
/// exercise_id, notes, sets`) — no display name. See `train_models.dart`'s
/// own top doc comment for why [TrainExercisePerformance.exerciseName]
/// falls back to the raw [exerciseId] here rather than a fabricated
/// label: no `GET /exercises`-shaped endpoint exists anywhere in this
/// backend to resolve one (confirmed by `docs/adr/0048-train-repository-
/// integration.md`'s own research). `targetSets`/`targetReps`/
/// `targetWeight` are left `null` — `ExercisePerformanceResponse` carries
/// no progression-engine suggestion at all; inventing one here would be
/// exactly the "never duplicate backend business logic" violation this
/// phase's own instructions forbid.
class ExercisePerformanceDto {
  const ExercisePerformanceDto({
    required this.performanceId,
    required this.exerciseId,
    required this.notes,
    required this.sets,
  });

  factory ExercisePerformanceDto.fromJson(Map<String, dynamic> json) {
    return ExercisePerformanceDto(
      performanceId: json.requireString('performance_id'),
      exerciseId: json.requireString('exercise_id'),
      notes: json.requireString('notes'),
      sets: json
          .requireList('sets')
          .cast<Map<String, dynamic>>()
          .map(ExerciseSetDto.fromJson)
          .toList(growable: false),
    );
  }

  final String performanceId;
  final String exerciseId;
  final String notes;
  final List<ExerciseSetDto> sets;

  TrainExercisePerformance toDomain() {
    return TrainExercisePerformance(
      performanceId: performanceId,
      exerciseId: exerciseId,
      exerciseName: exerciseId,
      notes: notes,
      sets: sets.map((ExerciseSetDto s) => s.toDomain()).toList(growable: false),
    );
  }
}

/// Mirrors `WorkoutSessionResponse` exactly (`backend/app/api/schemas/
/// workout.py`), except [workoutName] — the response carries only
/// `workout_id`, never a name (see `train_models.dart`'s own
/// [TrainSession.workoutName] doc comment for why that is resolved by a
/// second real fetch in `ApiTrainRepository`, not fabricated here).
/// [toDomain] therefore takes [workoutName] and [lastMutationWarnings] as
/// parameters rather than fields this DTO itself owns — both are only
/// known to the repository, never to a raw `GET .../{id}` response body.
class TrainSessionDto {
  const TrainSessionDto({
    required this.sessionId,
    required this.workoutId,
    required this.userId,
    required this.status,
    required this.sessionDate,
    required this.plannedAt,
    required this.notes,
    required this.durationSeconds,
    required this.completionPercentage,
    required this.rating,
    required this.startedAt,
    required this.completedAt,
    required this.abandonedAt,
    required this.exercisePerformances,
  });

  factory TrainSessionDto.fromJson(Map<String, dynamic> json) {
    return TrainSessionDto(
      sessionId: json.requireString('session_id'),
      workoutId: json.requireString('workout_id'),
      userId: json.requireString('user_id'),
      status: json.requireString('status'),
      sessionDate: parseApiDate(json.requireString('session_date')),
      plannedAt: parseApiDateTime(json.requireString('planned_at')),
      notes: json.requireString('notes'),
      durationSeconds: json.optionalDouble('duration_seconds'),
      completionPercentage: json.optionalDouble('completion_percentage'),
      rating: json.optionalInt('rating'),
      startedAt: _optionalDateTime(json.optionalString('started_at')),
      completedAt: _optionalDateTime(json.optionalString('completed_at')),
      abandonedAt: _optionalDateTime(json.optionalString('abandoned_at')),
      exercisePerformances: json
          .requireList('exercise_performances')
          .cast<Map<String, dynamic>>()
          .map(ExercisePerformanceDto.fromJson)
          .toList(growable: false),
    );
  }

  final String sessionId;
  final String workoutId;
  final String userId;
  final String status;
  final DateTime sessionDate;
  final DateTime plannedAt;
  final String notes;
  final double? durationSeconds;
  final double? completionPercentage;
  final int? rating;
  final DateTime? startedAt;
  final DateTime? completedAt;
  final DateTime? abandonedAt;
  final List<ExercisePerformanceDto> exercisePerformances;

  TrainSession toDomain({
    required String workoutName,
    List<String> lastMutationWarnings = const <String>[],
  }) {
    return TrainSession(
      sessionId: sessionId,
      workoutId: workoutId,
      workoutName: workoutName,
      status: SessionStatus.fromWire(status),
      sessionDate: sessionDate,
      exercisePerformances: exercisePerformances
          .map((ExercisePerformanceDto p) => p.toDomain())
          .toList(growable: false),
      notes: notes,
      durationSeconds: durationSeconds,
      completionPercentage: completionPercentage,
      rating: rating,
      startedAt: startedAt,
      completedAt: completedAt,
      abandonedAt: abandonedAt,
      lastMutationWarnings: lastMutationWarnings,
    );
  }

  static DateTime? _optionalDateTime(String? value) =>
      value == null ? null : parseApiDateTime(value);
}
