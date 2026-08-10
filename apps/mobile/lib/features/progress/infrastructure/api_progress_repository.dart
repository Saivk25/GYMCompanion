import '../../../core/cache/cache.dart';
import '../../../core/mapping/mapping.dart';
import '../../../core/network/network.dart';
import '../application/progress_controller.dart';
import '../domain/progress_models.dart';
import 'dto/nutrition_summary_entry_dto.dart';
import 'dto/progress_entry_dto.dart';
import 'dto/readiness_summary_entry_dto.dart';

/// The real [ProgressRepository] — the fifth `ApiXRepository` this
/// project has built (`docs/adr/0050-progress-repository-integration.md`),
/// on the same `ApiClient` (`docs/adr/0043`) and shared mapping
/// convention (`docs/adr/0045`) Today/Readiness/Train/Fuel already
/// proved. Wired in `lib/main.dart`, replacing [MockProgressRepository];
/// `ProgressHomeController` and every Progress screen are unchanged.
///
/// ## One endpoint list, three real surfaces
///
/// [fetchHome] issues three parallel `GET`s — `/api/v1/progress`,
/// `/api/v1/nutrition`, `/api/v1/readiness` — the same three endpoints
/// Progress/Fuel/Readiness/Today already use individually, none of them
/// Progress-specific. [measurements] is a direct map of every real
/// `ProgressResponse`, sorted newest-first (no backend ordering
/// guarantee — ADR 0042 Part 2's own finding, reused here). [nutritionWeek]/
/// [readinessWeek] are real client-side aggregations over the full,
/// unfiltered nutrition/readiness lists — `aggregateNutritionWeek`/
/// `aggregateReadinessWeek` (`dto/nutrition_summary_entry_dto.dart`,
/// `dto/readiness_summary_entry_dto.dart`) sum/select real per-day
/// values, never a fabricated trend. `progress_models.dart`'s own
/// library doc comment already anticipated this exact shape ("each
/// backed by the same real backend concept... summarized the way a real
/// trend endpoint would summarize them") before this class existed.
///
/// ## `unit`/`source` are hardcoded on write, not invented
///
/// `RecordProgressRequest.unit`/`.source` are *required* fields
/// (`backend/app/api/schemas/progress.py`) — unlike Readiness's/Fuel's
/// optional `source`, there is no way to omit either here. This
/// repository sends `unit: 'metric'`, `source: 'manual'` on every
/// [logMeasurement] call — not a new decision this phase invented:
/// [MockProgressRepository] already hardcoded the identical two values
/// on every entry it ever constructed, and `MeasurementMetric
/// .unitSuffix`'s own doc comment already discloses that no
/// personalized unit preference exists anywhere in this client. `source:
/// 'manual'` is not a guess either — every entry this client can create
/// today genuinely was typed in by hand, so it is the one honestly
/// correct value, not a fabricated default the way a computed score
/// would be. Neither value is exposed as a new [ProgressRepository]
/// parameter — the interface did not change.
///
/// ## Logged entries are honest echoes, plus real warnings
///
/// `POST /api/v1/progress` returns `IdResponse{id, warnings}` — the same
/// constraint every prior `ApiXRepository`'s own mutation faced. The
/// echoed [ProgressEntry] inside the returned [ProgressLogResult] is
/// built from exactly the submitted parameters plus the real assigned
/// `id`, since `LogMeasurementScreen`/`ProgressHomeController
/// .logMeasurement` both discard it and immediately re-fetch
/// [fetchHome] instead (confirmed by reading both call sites). Unlike
/// this repository's first draft, `warnings` is *not* discarded:
/// `RecordProgressHandler` (`backend/app/application/progress/handlers/
/// record_progress_handler.py`) really does run
/// `ProgressEvaluationRuleEngine` (`ConsistencyRule`/`PlateauRule`/
/// `MeasurementTrendRule`) against the user's full check-in history on
/// every write and returns its findings as `ApplicationResult.warnings`
/// — silently dropping them would have discarded real advisory data.
/// See [ProgressLogResult]'s own doc comment (`progress_models.dart`)
/// for why those warnings render inline on Progress Home
/// (`lastLogWarnings`) rather than flowing into `CoachSignalLog`:
/// `CoachModule` (`lib/shared/domain/coach_signal.dart`) is a
/// deliberately closed 3-value enum that excludes Progress by design
/// (ADR 0041), confirmed by reading that enum's own doc comment, so a
/// 4th synthetic category was not invented to force a fit.
///
/// ## Only one backend capability gap remains
///
/// Every field `ProgressHomeViewState` renders maps to something real:
/// [measurements] to `GET /api/v1/progress`, [nutritionWeek]/
/// [readinessWeek] to real client-side sums/selections over
/// `GET /api/v1/nutrition`/`GET /api/v1/readiness`, and now
/// `lastLogWarnings` to the real rule-engine output above.
/// `ProgressHomeScreen`'s Workout/Reports/Correlations sections were
/// already disclosed, permanent `NotConnectedPlaceholder`s before this
/// phase — no backend analytics/report/photo/correlation route exists
/// anywhere (`ProgressRepository`'s own doc comment) — and remain
/// untouched; this repository adds no method for any of them.
///
/// ## `fetchHome` is now read-through cached (Step 4)
///
/// `docs/adr/0052-offline-caching.md` — [fetchHome] reuses the shared
/// `readThroughCache` policy (`core/cache/read_through_cache.dart`),
/// caching the raw three-endpoint JSON bundle as one unit: serves a
/// fresh-enough cached bundle immediately while revalidating in the
/// background, falls back to the last cached bundle on a real network
/// failure ([ProgressHomeViewState.isOffline] now genuinely reflects
/// this rather than always being `false`), and otherwise fetches live
/// and writes through. [logMeasurement] is a mutation, not a read —
/// deliberately not cached, per this phase's own scope. It does,
/// however, invalidate [fetchHome]'s own cache entry on success
/// (`LocalCache.invalidate`) so `ProgressHomeController`'s existing
/// mutate-then-refetch call site sees the real new entry instead of a
/// stale cached bundle.
class ApiProgressRepository implements ProgressRepository {
  ApiProgressRepository(this._client, this._cache);

  final ApiClient _client;
  final LocalCache _cache;

  static const String _cacheKey = 'progress_home';

  @override
  Future<ProgressHomeViewState> fetchHome() {
    return readThroughCache<ProgressHomeViewState>(
      cache: _cache,
      key: _cacheKey,
      maxAge: kCacheFreshDuration,
      fetchRawJson: _fetchRawJson,
      build: _buildViewState,
    );
  }

  Future<Object?> _fetchRawJson() async {
    final List<List<dynamic>> results = await Future.wait(<Future<List<dynamic>>>[
      _client.getList('${ApiConfig.v1PathPrefix}/progress'),
      _client.getList('${ApiConfig.v1PathPrefix}/nutrition'),
      _client.getList('${ApiConfig.v1PathPrefix}/readiness'),
    ]);
    return <String, dynamic>{
      'progress': results[0],
      'nutrition': results[1],
      'readiness': results[2],
    };
  }

  ProgressHomeViewState _buildViewState(Object? rawJson, {required bool isOffline}) {
    final Map<String, dynamic> bundle = rawJson! as Map<String, dynamic>;

    final List<ProgressEntry> measurements = (bundle['progress']! as List<dynamic>)
        .cast<Map<String, dynamic>>()
        .map(ProgressEntryDto.fromJson)
        .map((ProgressEntryDto dto) => dto.toDomain())
        .toList()
      ..sort((ProgressEntry a, ProgressEntry b) => b.progressDate.compareTo(a.progressDate));

    final List<NutritionSummaryEntryDto> nutritionEntries = (bundle['nutrition']! as List<dynamic>)
        .cast<Map<String, dynamic>>()
        .map(NutritionSummaryEntryDto.fromJson)
        .toList(growable: false);
    final List<ReadinessSummaryEntryDto> readinessEntries = (bundle['readiness']! as List<dynamic>)
        .cast<Map<String, dynamic>>()
        .map(ReadinessSummaryEntryDto.fromJson)
        .toList(growable: false);

    final DateTime today = DateTime.now();

    return ProgressHomeViewState(
      asOf: today,
      measurements: measurements,
      nutritionWeek: aggregateNutritionWeek(nutritionEntries, today),
      readinessWeek: aggregateReadinessWeek(readinessEntries, today),
      hasLoggedAnyMeasurementEver: measurements.isNotEmpty,
      isOffline: isOffline,
    );
  }

  @override
  Future<ProgressLogResult> logMeasurement({
    required DateTime date,
    double? bodyWeight,
    double? bodyFatPercentage,
    double? leanBodyMass,
    double? muscleMass,
    double? waist,
    double? chest,
    double? hip,
    double? arm,
    double? thigh,
    double? calf,
    double? neck,
    String? notes,
  }) async {
    final Map<String, dynamic> body = <String, dynamic>{
      'progress_date': apiDateString(date),
      // Required by RecordProgressRequest; see this class's own doc
      // comment for why these two literal values are honest, not
      // invented.
      'unit': 'metric',
      'source': 'manual',
      if (bodyWeight != null) 'body_weight': bodyWeight,
      if (bodyFatPercentage != null) 'body_fat_percentage': bodyFatPercentage,
      if (leanBodyMass != null) 'lean_body_mass': leanBodyMass,
      if (muscleMass != null) 'muscle_mass': muscleMass,
      if (waist != null) 'waist': waist,
      if (chest != null) 'chest': chest,
      if (hip != null) 'hip': hip,
      if (arm != null) 'arm': arm,
      if (thigh != null) 'thigh': thigh,
      if (calf != null) 'calf': calf,
      if (neck != null) 'neck': neck,
      if (notes != null) 'notes': notes,
    };

    final Map<String, dynamic> json = await _client.post(
      '${ApiConfig.v1PathPrefix}/progress',
      body: body,
    );
    final String progressId = json.requireString('id');
    final List<String> warnings =
        (json.optionalList('warnings') ?? const <dynamic>[]).cast<String>();

    // `ProgressHomeController.logMeasurement` refetches `fetchHome()`
    // immediately after this returns and expects the new entry to be
    // there — see `LocalCache.invalidate`'s own doc comment.
    await _cache.invalidate(_cacheKey);

    final ProgressEntry entry = ProgressEntry(
      progressId: progressId,
      progressDate: date,
      recordedAt: DateTime.now(),
      unit: 'metric',
      source: 'manual',
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
      notes: notes ?? '',
    );

    return ProgressLogResult(entry: entry, warnings: warnings);
  }
}
