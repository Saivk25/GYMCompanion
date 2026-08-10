import '../../../../core/mapping/mapping.dart';
import '../../domain/progress_models.dart';

/// A narrow read of `ReadinessResponse` (`backend/app/api/schemas/
/// readiness.py`) — only the four fields [ReadinessDayEntry] is built
/// from (`readiness_date`, `recorded_at`, `sleep_duration_seconds`,
/// `resting_heart_rate`, `heart_rate_variability`), per `docs/adr/0045`'s
/// "a DTO models what a feature consumes" rule. Deliberately not
/// `ReadinessEntryDto` reused across a feature boundary — see
/// `progress_models.dart`'s own library doc comment for why Progress
/// owns this narrower view type and its own parsing independently of
/// Readiness's.
class ReadinessSummaryEntryDto {
  const ReadinessSummaryEntryDto({
    required this.readinessDate,
    required this.recordedAt,
    required this.sleepDurationSeconds,
    required this.restingHeartRate,
    required this.heartRateVariability,
  });

  factory ReadinessSummaryEntryDto.fromJson(Map<String, dynamic> json) {
    return ReadinessSummaryEntryDto(
      readinessDate: parseApiDate(json.requireString('readiness_date')),
      recordedAt: parseApiDateTime(json.requireString('recorded_at')),
      sleepDurationSeconds: json.optionalDouble('sleep_duration_seconds'),
      restingHeartRate: json.optionalDouble('resting_heart_rate'),
      heartRateVariability: json.optionalDouble('heart_rate_variability'),
    );
  }

  final DateTime readinessDate;
  final DateTime recordedAt;
  final double? sleepDurationSeconds;
  final double? restingHeartRate;
  final double? heartRateVariability;
}

/// One real entry per date is the common case, but the backend allows
/// more than one `Readiness` record per day (no uniqueness constraint on
/// `readiness_date` — confirmed by reading `backend/app/domain/
/// readiness/readiness.py`), so this is many-to-*at-most-one*, not
/// strictly 1:1 — per `docs/adr/0045`'s own convention, a small top-level
/// function in the same file rather than a `toDomain()` on the DTO
/// itself. When more than one entry shares a date, the most recently
/// *recorded* one wins (`recordedAt`, not [readinessDate], since every
/// candidate already shares the same date) — the same "authoritative
/// latest" tie-break `ApiTrainRepository._fetchFullSession` uses for
/// resolving one value from potentially-multiple real records.
///
/// Builds exactly 7 [ReadinessDayEntry]s, oldest first, mirroring
/// [aggregateNutritionWeek]'s identical window shape (`nutrition_summary_
/// entry_dto.dart`) and `MockProgressRepository._seedReadinessWeek`'s own
/// fixed-7-day-window.
List<ReadinessDayEntry> aggregateReadinessWeek(
  List<ReadinessSummaryEntryDto> entries,
  DateTime today,
) {
  return List<ReadinessDayEntry>.generate(7, (int i) {
    final DateTime date = today.subtract(Duration(days: 6 - i));
    final String dateKey = apiDateString(date);
    final List<ReadinessSummaryEntryDto> dayEntries = entries
        .where((ReadinessSummaryEntryDto e) => apiDateString(e.readinessDate) == dateKey)
        .toList();

    if (dayEntries.isEmpty) {
      return ReadinessDayEntry(date: date, hasAnyEntry: false);
    }

    dayEntries.sort(
      (ReadinessSummaryEntryDto a, ReadinessSummaryEntryDto b) =>
          b.recordedAt.compareTo(a.recordedAt),
    );
    final ReadinessSummaryEntryDto latest = dayEntries.first;

    return ReadinessDayEntry(
      date: date,
      hasAnyEntry: true,
      sleepHours: latest.sleepDurationSeconds == null ? null : latest.sleepDurationSeconds! / 3600,
      restingHeartRate: latest.restingHeartRate,
      heartRateVariability: latest.heartRateVariability,
    );
  });
}
