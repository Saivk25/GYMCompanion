import '../../../../core/mapping/mapping.dart';

/// A minimal projection of `ReadinessResponse`
/// (`backend/app/api/schemas/readiness.py`) — `ApiTodayRepository` only
/// ever needs one fact from each entry in `GET /api/v1/readiness`:
/// which calendar date it was recorded for, to answer "has today's
/// check-in already been submitted." See `docs/adr/0045-shared-api-
/// mapping-convention.md`'s "a DTO models the fields a feature actually
/// consumes" convention — a full `ReadinessDto` mirroring every field
/// (sleep, energy, stress, ...) belongs to Readiness's own future
/// `ApiReadinessRepository`, not here.
class ReadinessSummaryDto {
  const ReadinessSummaryDto({required this.readinessDate});

  final DateTime readinessDate;

  factory ReadinessSummaryDto.fromJson(Map<String, dynamic> json) {
    return ReadinessSummaryDto(
      readinessDate: parseApiDate(json.requireString('readiness_date')),
    );
  }
}
