import '../../../../core/mapping/mapping.dart';
import '../../domain/train_models.dart';

/// Mirrors `WorkoutResponse` (`backend/app/api/schemas/workout.py`)
/// field-for-field, per `docs/adr/0045-shared-api-mapping-convention.md`.
/// `cancelled_at` is read but has no [TrainWorkout] field to carry it to —
/// `status` already distinguishes cancelled from every other state, and
/// no Train screen renders a cancellation timestamp, matching this
/// convention's "a DTO reads every real field; a domain type carries only
/// what a feature consumes" split (see `ADR 0045` and `ADR 0047`'s own
/// `ReadinessEntryDto` for the same pattern applied there).
class TrainWorkoutDto {
  const TrainWorkoutDto({
    required this.workoutId,
    required this.userId,
    required this.status,
    required this.name,
    required this.plannedDate,
    required this.plannedAt,
    required this.goal,
    required this.notes,
    required this.durationSeconds,
    required this.startedAt,
    required this.completedAt,
    required this.cancelledAt,
  });

  factory TrainWorkoutDto.fromJson(Map<String, dynamic> json) {
    return TrainWorkoutDto(
      workoutId: json.requireString('workout_id'),
      userId: json.requireString('user_id'),
      status: json.requireString('status'),
      name: json.requireString('name'),
      plannedDate: parseApiDate(json.requireString('planned_date')),
      plannedAt: parseApiDateTime(json.requireString('planned_at')),
      goal: json.optionalString('goal'),
      notes: json.optionalString('notes'),
      durationSeconds: json.optionalDouble('duration_seconds'),
      startedAt: _optionalDateTime(json.optionalString('started_at')),
      completedAt: _optionalDateTime(json.optionalString('completed_at')),
      cancelledAt: _optionalDateTime(json.optionalString('cancelled_at')),
    );
  }

  final String workoutId;
  final String userId;
  final String status;
  final String name;
  final DateTime plannedDate;
  final DateTime plannedAt;
  final String? goal;
  final String? notes;
  final double? durationSeconds;
  final DateTime? startedAt;
  final DateTime? completedAt;
  final DateTime? cancelledAt;

  TrainWorkout toDomain() {
    return TrainWorkout(
      workoutId: workoutId,
      name: name,
      plannedDate: plannedDate,
      status: WorkoutStatus.fromWire(status),
      goal: goal,
      notes: notes,
      durationSeconds: durationSeconds,
      startedAt: startedAt,
      completedAt: completedAt,
    );
  }

  static DateTime? _optionalDateTime(String? value) =>
      value == null ? null : parseApiDateTime(value);
}
