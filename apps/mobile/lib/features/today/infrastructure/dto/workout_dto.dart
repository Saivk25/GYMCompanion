import '../../../../core/mapping/mapping.dart';

/// A direct, honest projection of `WorkoutResponse`
/// (`backend/app/api/schemas/workout.py`) — only the fields
/// `ApiTodayRepository` actually needs to decide today's session state
/// (see `docs/adr/0045-shared-api-mapping-convention.md`'s "a DTO
/// models the fields a feature actually consumes" convention).
/// [status]/[name]/[plannedDate]/[goal]/[notes] all map 1:1 from the
/// backend field of the same name (after camelCase conversion) — none
/// are derived or reinterpreted.
class WorkoutDto {
  const WorkoutDto({
    required this.workoutId,
    required this.status,
    required this.name,
    required this.plannedDate,
    this.goal,
    this.notes,
  });

  final String workoutId;

  /// The raw wire value of `WorkoutStatus`
  /// (`backend/app/domain/workout/enums.py`): `"planned"`,
  /// `"in_progress"`, `"completed"`, or `"cancelled"`. Kept as the raw
  /// string here, mapped to [SessionCardStatus] by
  /// `ApiTodayRepository._sessionStatusFor` — this DTO does not define
  /// its own enum for it, since nothing outside that one mapping site
  /// reads it.
  final String status;

  final String name;
  final DateTime plannedDate;
  final String? goal;
  final String? notes;

  factory WorkoutDto.fromJson(Map<String, dynamic> json) {
    return WorkoutDto(
      workoutId: json.requireString('workout_id'),
      status: json.requireString('status'),
      name: json.requireString('name'),
      plannedDate: parseApiDate(json.requireString('planned_date')),
      goal: json.optionalString('goal'),
      notes: json.optionalString('notes'),
    );
  }
}
