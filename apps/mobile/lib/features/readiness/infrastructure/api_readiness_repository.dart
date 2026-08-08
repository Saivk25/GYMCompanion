import '../../../core/mapping/mapping.dart';
import '../../../core/network/network.dart';
import '../application/readiness_controller.dart';
import '../domain/readiness_models.dart';
import 'dto/readiness_entry_dto.dart';

/// The real [ReadinessRepository] — the second `ApiXRepository` this
/// project has built (`docs/adr/0047-readiness-repository-integration.md`),
/// on the same `ApiClient` (`docs/adr/0043`) and shared mapping
/// convention (`docs/adr/0045`) `ApiTodayRepository` already proved.
/// Wired in `lib/main.dart`, replacing [MockReadinessRepository];
/// `ReadinessHomeController` and every Readiness screen are unchanged —
/// same "swap the provider override" seam every prior feature has used.
///
/// ## Two real endpoints, no interface change
///
/// [fetchHome] → `GET /api/v1/readiness` (`ListReadinessHandler`), the
/// full unfiltered list, sorted newest-first client-side (the backend
/// makes no ordering guarantee — ADR 0042 Part 2's own "no pagination
/// or filtering exists anywhere" finding). [submitCheckIn] →
/// `POST /api/v1/readiness` (`RecordReadinessHandler`), which evaluates
/// the real `ReadinessRuleEngine` once, server-side, after commit, and
/// returns its recommendations as `IdResponse.warnings` — the exact,
/// non-fabricated strings this method returns unchanged. Nothing here
/// computes, thresholds, or re-derives a warning; a client-side
/// reimplementation of `ReadinessRuleEngine` is exactly what this
/// phase's "never duplicate backend business logic" rule forbids.
/// [ReadinessRepository]'s own interface did not change — no update or
/// delete method was added, because no Readiness screen has an edit or
/// delete affordance today (`ReadinessHomeScreen`'s "Edit" action
/// re-opens the check-in flow, i.e. submits a new entry, exactly as it
/// already did against [MockReadinessRepository]).
///
/// ## `submitCheckIn`'s returned entry is an honest echo, not a second
/// fetch
///
/// `POST /api/v1/readiness` returns only `IdResponse{id, warnings}` —
/// never the full created resource (`backend/app/api/schemas/
/// common.py`'s own `IdResponse` doc comment: "deliberately not the
/// full updated resource"). No current caller reads
/// [ReadinessCheckInResult.entry] (`ReadinessCheckInScreen` awaits
/// [ReadinessHomeController.submitCheckIn] and discards its result;
/// [ReadinessHomeController] itself re-fetches [fetchHome] immediately
/// after — the real "mutate → refetch" this phase's own instruction
/// asks for, already implemented at the controller level before this
/// class existed), so the entry returned here is built from exactly the
/// parameters the caller passed plus the real `id` the backend
/// assigned — never fabricated, never guessed, and never a second
/// network round trip for a value nothing reads. `source` is left
/// `null`, matching this method's own request body: `[submitCheckIn]`
/// has no `source` parameter, so the request never sends one, and
/// `Readiness.record()` (`backend/app/domain/readiness/readiness.py`)
/// defaults an omitted `source` to `None`, never `MANUAL` — echoing
/// `null` here is the accurate reflection of what was actually
/// submitted. `recordedAt` is a local `DateTime.now()` approximation,
/// not the authoritative server-assigned timestamp; harmless while
/// unused, and any future caller that needs the real value should fetch
/// `GET /api/v1/readiness/{id}` instead of trusting this field.
class ApiReadinessRepository implements ReadinessRepository {
  ApiReadinessRepository(this._client);

  final ApiClient _client;

  @override
  Future<ReadinessHomeViewState> fetchHome() async {
    final List<dynamic> raw = await _client.getList('${ApiConfig.v1PathPrefix}/readiness');
    final List<ReadinessEntry> entries = raw
        .cast<Map<String, dynamic>>()
        .map(ReadinessEntryDto.fromJson)
        .map((ReadinessEntryDto dto) => dto.toDomain())
        .toList()
      ..sort((ReadinessEntry a, ReadinessEntry b) => b.readinessDate.compareTo(a.readinessDate));

    return ReadinessHomeViewState(
      asOf: DateTime.now(),
      entries: entries,
      hasCheckedInEver: entries.isNotEmpty,
    );
  }

  @override
  Future<ReadinessCheckInResult> submitCheckIn({
    required DateTime date,
    Duration? sleepDuration,
    int? sleepQuality,
    int? energyLevel,
    int? stressLevel,
    int? sorenessLevel,
    double? restingHeartRate,
    double? heartRateVariability,
    String? notes,
  }) async {
    final Map<String, dynamic> body = <String, dynamic>{
      'readiness_date': apiDateString(date),
      if (sleepDuration != null) 'sleep_duration_seconds': sleepDuration.inMilliseconds / 1000,
      if (sleepQuality != null) 'sleep_quality': sleepQuality,
      if (energyLevel != null) 'energy_level': energyLevel,
      if (stressLevel != null) 'stress_level': stressLevel,
      if (sorenessLevel != null) 'soreness_level': sorenessLevel,
      if (restingHeartRate != null) 'resting_heart_rate': restingHeartRate,
      if (heartRateVariability != null) 'heart_rate_variability': heartRateVariability,
      if (notes != null) 'notes': notes,
    };

    final Map<String, dynamic> json = await _client.post(
      '${ApiConfig.v1PathPrefix}/readiness',
      body: body,
    );
    final String readinessId = json.requireString('id');
    final List<String> warnings =
        (json.optionalList('warnings') ?? const <dynamic>[]).cast<String>();

    final ReadinessEntry entry = ReadinessEntry(
      readinessId: readinessId,
      readinessDate: date,
      recordedAt: DateTime.now(),
      sleepDuration: sleepDuration,
      sleepQuality: sleepQuality,
      energyLevel: energyLevel,
      stressLevel: stressLevel,
      sorenessLevel: sorenessLevel,
      restingHeartRate: restingHeartRate,
      heartRateVariability: heartRateVariability,
      notes: notes ?? '',
    );

    return ReadinessCheckInResult(entry: entry, warnings: warnings);
  }
}
