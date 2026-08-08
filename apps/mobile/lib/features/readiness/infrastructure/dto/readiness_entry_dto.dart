import '../../../../core/mapping/mapping.dart';
import '../../domain/readiness_models.dart';

/// A direct, complete projection of `ReadinessResponse`
/// (`backend/app/api/schemas/readiness.py`) — unlike Today's own
/// `ReadinessSummaryDto` (which only reads `readiness_date`), this
/// module's own repository is the real owner of every readiness field,
/// so this DTO mirrors the full backend response, per `docs/adr/0045-
/// shared-api-mapping-convention.md`'s "a DTO models the fields a
/// feature actually consumes" rule — here, that's all of them.
class ReadinessEntryDto {
  const ReadinessEntryDto({
    required this.readinessId,
    required this.readinessDate,
    required this.recordedAt,
    this.source,
    this.sleepDurationSeconds,
    this.sleepQuality,
    this.energyLevel,
    this.stressLevel,
    this.sorenessLevel,
    this.restingHeartRate,
    this.heartRateVariability,
    this.notes = '',
    this.updatedAt,
  });

  final String readinessId;
  final DateTime readinessDate;
  final DateTime recordedAt;
  final String? source;
  final double? sleepDurationSeconds;
  final int? sleepQuality;
  final int? energyLevel;
  final int? stressLevel;
  final int? sorenessLevel;
  final double? restingHeartRate;
  final double? heartRateVariability;
  final String notes;
  final DateTime? updatedAt;

  factory ReadinessEntryDto.fromJson(Map<String, dynamic> json) {
    return ReadinessEntryDto(
      readinessId: json.requireString('readiness_id'),
      readinessDate: parseApiDate(json.requireString('readiness_date')),
      recordedAt: parseApiDateTime(json.requireString('recorded_at')),
      source: json.optionalString('source'),
      sleepDurationSeconds: json.optionalDouble('sleep_duration_seconds'),
      sleepQuality: json.optionalInt('sleep_quality'),
      energyLevel: json.optionalInt('energy_level'),
      stressLevel: json.optionalInt('stress_level'),
      sorenessLevel: json.optionalInt('soreness_level'),
      restingHeartRate: json.optionalDouble('resting_heart_rate'),
      heartRateVariability: json.optionalDouble('heart_rate_variability'),
      notes: json.optionalString('notes') ?? '',
      updatedAt: json.optionalString('updated_at') != null
          ? parseApiDateTime(json.requireString('updated_at'))
          : null,
    );
  }

  /// The domain mapping lives here, on the DTO itself — no separate
  /// mapper class, per `docs/adr/0045`'s own convention.
  ReadinessEntry toDomain() {
    return ReadinessEntry(
      readinessId: readinessId,
      readinessDate: readinessDate,
      recordedAt: recordedAt,
      source: source != null ? ReadinessSource.fromWire(source!) : null,
      sleepDuration: sleepDurationSeconds != null
          ? Duration(milliseconds: (sleepDurationSeconds! * 1000).round())
          : null,
      sleepQuality: sleepQuality,
      energyLevel: energyLevel,
      stressLevel: stressLevel,
      sorenessLevel: sorenessLevel,
      restingHeartRate: restingHeartRate,
      heartRateVariability: heartRateVariability,
      notes: notes,
      updatedAt: updatedAt,
    );
  }
}
