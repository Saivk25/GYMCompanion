import '../../../../core/mapping/mapping.dart';
import '../../domain/progress_models.dart';

/// Mirrors `ProgressResponse` (`backend/app/api/schemas/progress.py`)
/// field-for-field, per `docs/adr/0045-shared-api-mapping-convention.md`
/// — this module is the real owner of every progress field, the same
/// "consumes everything" posture `ReadinessEntryDto`/`FuelEntryDto`
/// already established for a feature that owns its own full response
/// shape.
///
/// `unit`/`source` are read and passed through as the backend's own raw
/// wire strings (`"metric"`/`"imperial"`, `"manual"`/`"smart_scale"`/
/// `"calculated"`), not mapped through a `fromWire` enum factory —
/// [ProgressEntry.unit]/[ProgressEntry.source] are themselves plain
/// `String?` fields (`progress_models.dart`'s own doc comment never
/// promoted them to real Dart enums the way `MealType`/`NutritionSource`
/// were), so there is no enum to map onto here; this DTO does not
/// introduce one speculatively.
class ProgressEntryDto {
  const ProgressEntryDto({
    required this.progressId,
    required this.userId,
    required this.progressDate,
    required this.unit,
    required this.source,
    required this.recordedAt,
    required this.bodyWeight,
    required this.bodyFatPercentage,
    required this.leanBodyMass,
    required this.muscleMass,
    required this.waist,
    required this.chest,
    required this.hip,
    required this.arm,
    required this.thigh,
    required this.calf,
    required this.neck,
    required this.notes,
    required this.updatedAt,
  });

  factory ProgressEntryDto.fromJson(Map<String, dynamic> json) {
    return ProgressEntryDto(
      progressId: json.requireString('progress_id'),
      userId: json.requireString('user_id'),
      progressDate: parseApiDate(json.requireString('progress_date')),
      unit: json.requireString('unit'),
      source: json.requireString('source'),
      recordedAt: parseApiDateTime(json.requireString('recorded_at')),
      bodyWeight: json.optionalDouble('body_weight'),
      bodyFatPercentage: json.optionalDouble('body_fat_percentage'),
      leanBodyMass: json.optionalDouble('lean_body_mass'),
      muscleMass: json.optionalDouble('muscle_mass'),
      waist: json.optionalDouble('waist'),
      chest: json.optionalDouble('chest'),
      hip: json.optionalDouble('hip'),
      arm: json.optionalDouble('arm'),
      thigh: json.optionalDouble('thigh'),
      calf: json.optionalDouble('calf'),
      neck: json.optionalDouble('neck'),
      notes: json.requireString('notes'),
      updatedAt: _optionalDateTime(json.optionalString('updated_at')),
    );
  }

  final String progressId;
  final String userId;
  final DateTime progressDate;
  final String unit;
  final String source;
  final DateTime recordedAt;
  final double? bodyWeight;
  final double? bodyFatPercentage;
  final double? leanBodyMass;
  final double? muscleMass;
  final double? waist;
  final double? chest;
  final double? hip;
  final double? arm;
  final double? thigh;
  final double? calf;
  final double? neck;
  final String notes;
  final DateTime? updatedAt;

  ProgressEntry toDomain() {
    return ProgressEntry(
      progressId: progressId,
      progressDate: progressDate,
      recordedAt: recordedAt,
      unit: unit,
      source: source,
      bodyWeight: bodyWeight,
      bodyFatPercentage: bodyFatPercentage,
      leanBodyMass: leanBodyMass,
      muscleMass: muscleMass,
      waist: waist,
      chest: chest,
      hip: hip,
      arm: arm,
      thigh: thigh,
      calf: calf,
      neck: neck,
      notes: notes,
      updatedAt: updatedAt,
    );
  }

  static DateTime? _optionalDateTime(String? value) =>
      value == null ? null : parseApiDateTime(value);
}
