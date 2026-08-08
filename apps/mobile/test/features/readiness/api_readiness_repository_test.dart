import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/core/mapping/mapping.dart';
import 'package:gym_companion_mobile/core/network/network.dart';
import 'package:gym_companion_mobile/features/readiness/domain/readiness_models.dart';
import 'package:gym_companion_mobile/features/readiness/infrastructure/api_readiness_repository.dart';

import '../../core/network/fakes/fake_http_client_adapter.dart';

/// [ApiReadinessRepository] against the same hand-written
/// [FakeHttpClientAdapter] `test/core/network/`'s and `ApiTodayRepository`'s
/// own tests already established — see that file's own doc comment for
/// why (proves the real `ApiClient`/`Dio` pipeline, not a hand-rolled
/// repository-level fake).
ApiClient _clientWith(HttpClientAdapter adapter) {
  final Dio dio = Dio(BaseOptions(baseUrl: 'http://test'));
  dio.httpClientAdapter = adapter;
  return ApiClient(dio: dio);
}

Map<String, dynamic> _entryJson({
  String id = 'r1',
  required String readinessDate,
  String? source,
  double? sleepDurationSeconds,
  int? sleepQuality,
  int? energyLevel,
  int? stressLevel,
  int? sorenessLevel,
  double? restingHeartRate,
  double? heartRateVariability,
  String notes = '',
}) {
  return <String, dynamic>{
    'readiness_id': id,
    'user_id': 'u1',
    'readiness_date': readinessDate,
    'recorded_at': '2026-08-01T08:00:00+00:00',
    'source': source,
    'sleep_duration_seconds': sleepDurationSeconds,
    'sleep_quality': sleepQuality,
    'energy_level': energyLevel,
    'stress_level': stressLevel,
    'soreness_level': sorenessLevel,
    'resting_heart_rate': restingHeartRate,
    'heart_rate_variability': heartRateVariability,
    'notes': notes,
    'updated_at': null,
  };
}

void main() {
  group('fetchHome', () {
    test('maps a real GET /api/v1/readiness list to entries, newest first', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        FakeResponse(
          body: <Map<String, dynamic>>[
            _entryJson(id: 'r-old', readinessDate: '2026-08-01', sleepQuality: 6),
            _entryJson(id: 'r-new', readinessDate: '2026-08-05', sleepQuality: 8),
          ],
        ),
      ]);
      final ApiReadinessRepository repo = ApiReadinessRepository(_clientWith(adapter));

      final ReadinessHomeViewState state = await repo.fetchHome();

      expect(state.entries.length, 2);
      expect(state.entries.first.readinessId, 'r-new');
      expect(state.entries.last.readinessId, 'r-old');
      expect(state.hasCheckedInEver, isTrue);
      expect(state.lastCheckInWarnings, isEmpty);
      expect(state.isOffline, isFalse);
    });

    test('maps every real field, including enum source and sleep duration', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        FakeResponse(
          body: <Map<String, dynamic>>[
            _entryJson(
              readinessDate: '2026-08-05',
              source: 'manual',
              sleepDurationSeconds: 7.5 * 3600,
              sleepQuality: 7,
              energyLevel: 6,
              stressLevel: 4,
              sorenessLevel: 3,
              restingHeartRate: 54.0,
              heartRateVariability: 62.0,
              notes: 'Felt good',
            ),
          ],
        ),
      ]);
      final ApiReadinessRepository repo = ApiReadinessRepository(_clientWith(adapter));

      final ReadinessHomeViewState state = await repo.fetchHome();
      final ReadinessEntry entry = state.entries.single;

      expect(entry.source, ReadinessSource.manual);
      expect(entry.sleepDuration, const Duration(hours: 7, minutes: 30));
      expect(entry.sleepQuality, 7);
      expect(entry.energyLevel, 6);
      expect(entry.stressLevel, 4);
      expect(entry.sorenessLevel, 3);
      expect(entry.restingHeartRate, 54.0);
      expect(entry.heartRateVariability, 62.0);
      expect(entry.notes, 'Felt good');
    });

    test('zero entries has never checked in', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(body: <Map<String, dynamic>>[]),
      ]);
      final ApiReadinessRepository repo = ApiReadinessRepository(_clientWith(adapter));

      final ReadinessHomeViewState state = await repo.fetchHome();

      expect(state.hasCheckedInEver, isFalse);
    });

    test('a network failure propagates as ApiException', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(throwConnectionError: true),
      ]);
      final ApiReadinessRepository repo = ApiReadinessRepository(_clientWith(adapter));

      expect(repo.fetchHome(), throwsA(isA<ApiException>()));
    });
  });

  group('submitCheckIn', () {
    test('posts the submitted fields and returns the real warnings unchanged', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        FakeResponse(
          statusCode: 201,
          body: <String, dynamic>{
            'id': 'new-readiness-id',
            'warnings': <String>['[warning] Resting heart rate above baseline.'],
          },
        ),
      ]);
      final ApiReadinessRepository repo = ApiReadinessRepository(_clientWith(adapter));

      final ReadinessCheckInResult result = await repo.submitCheckIn(
        date: DateTime(2026, 8, 8),
        sleepDuration: const Duration(hours: 6),
        sleepQuality: 5,
        energyLevel: 4,
        stressLevel: 6,
        sorenessLevel: 5,
        restingHeartRate: 62.0,
        heartRateVariability: 45.0,
        notes: 'Rough night',
      );

      expect(result.warnings, <String>['[warning] Resting heart rate above baseline.']);
      expect(result.entry.readinessId, 'new-readiness-id');
      expect(result.entry.readinessDate, DateTime(2026, 8, 8));
      expect(result.entry.sleepDuration, const Duration(hours: 6));
      expect(result.entry.notes, 'Rough night');
      // Echoed, not fetched — see this repository's own doc comment for
      // why `source` is null: the request never sent one.
      expect(result.entry.source, isNull);

      final RequestOptions sent = adapter.requests.single;
      expect(sent.path, contains('/api/v1/readiness'));
      expect(sent.method, 'POST');
      final Map<String, dynamic> body = sent.data as Map<String, dynamic>;
      expect(body['readiness_date'], apiDateString(DateTime(2026, 8, 8)));
      expect(body['sleep_duration_seconds'], 6 * 3600);
      expect(body['sleep_quality'], 5);
      expect(body['notes'], 'Rough night');
      expect(body.containsKey('source'), isFalse);
    });

    test('an empty warnings list on a clean check-in is not an error', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(
          statusCode: 201,
          body: <String, dynamic>{'id': 'r-clean', 'warnings': <String>[]},
        ),
      ]);
      final ApiReadinessRepository repo = ApiReadinessRepository(_clientWith(adapter));

      final ReadinessCheckInResult result = await repo.submitCheckIn(date: DateTime(2026, 8, 8));

      expect(result.warnings, isEmpty);
    });

    test('omits unset fields from the request body entirely', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(
          statusCode: 201,
          body: <String, dynamic>{'id': 'r-minimal', 'warnings': <String>[]},
        ),
      ]);
      final ApiReadinessRepository repo = ApiReadinessRepository(_clientWith(adapter));

      await repo.submitCheckIn(date: DateTime(2026, 8, 8), sleepQuality: 8);

      final Map<String, dynamic> body = adapter.requests.single.data as Map<String, dynamic>;
      expect(body.containsKey('sleep_duration_seconds'), isFalse);
      expect(body.containsKey('energy_level'), isFalse);
      expect(body.containsKey('notes'), isFalse);
      expect(body['sleep_quality'], 8);
    });

    test('a validation failure (real 400) propagates as ApiException', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        FakeResponse(statusCode: 400, body: <String, dynamic>{'detail': 'invalid soreness_level'}),
      ]);
      final ApiReadinessRepository repo = ApiReadinessRepository(_clientWith(adapter));

      expect(
        repo.submitCheckIn(date: DateTime(2026, 8, 8)),
        throwsA(isA<ApiException>()),
      );
    });
  });
}
