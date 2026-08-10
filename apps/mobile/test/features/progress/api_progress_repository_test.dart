import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/core/mapping/mapping.dart';
import 'package:gym_companion_mobile/core/network/network.dart';
import 'package:gym_companion_mobile/features/progress/domain/progress_models.dart';
import 'package:gym_companion_mobile/features/progress/infrastructure/api_progress_repository.dart';

import '../../core/network/fakes/fake_http_client_adapter.dart';

/// [ApiProgressRepository] against the same hand-written
/// [FakeHttpClientAdapter] every prior `ApiXRepository`'s own test
/// already established — see that file's own doc comment for why
/// (proves the real `ApiClient`/`Dio` pipeline, not a hand-rolled
/// repository-level fake). [fetchHome] issues three real `GET`s in
/// parallel — `/api/v1/progress`, `/api/v1/nutrition`,
/// `/api/v1/readiness` — so every [FakeHttpClientAdapter] here supplies
/// exactly three queued responses, in that order.
ApiClient _clientWith(HttpClientAdapter adapter) {
  final Dio dio = Dio(BaseOptions(baseUrl: 'http://test'));
  dio.httpClientAdapter = adapter;
  return ApiClient(dio: dio);
}

Map<String, dynamic> _progressJson({
  String id = 'p1',
  required String progressDate,
  double? bodyWeight,
  double? bodyFatPercentage,
  double? waist,
  String notes = '',
}) {
  return <String, dynamic>{
    'progress_id': id,
    'user_id': 'u1',
    'progress_date': progressDate,
    'unit': 'metric',
    'source': 'manual',
    'recorded_at': '2026-08-08T08:00:00+00:00',
    'body_weight': bodyWeight,
    'body_fat_percentage': bodyFatPercentage,
    'lean_body_mass': null,
    'muscle_mass': null,
    'waist': waist,
    'chest': null,
    'hip': null,
    'arm': null,
    'thigh': null,
    'calf': null,
    'neck': null,
    'notes': notes,
    'updated_at': null,
  };
}

Map<String, dynamic> _nutritionJson({
  required String nutritionDate,
  double? protein,
  double? waterIntake,
}) {
  return <String, dynamic>{
    'nutrition_id': 'n1',
    'user_id': 'u1',
    'nutrition_date': nutritionDate,
    'recorded_at': '2026-08-08T08:00:00+00:00',
    'meal_type': null,
    'source': null,
    'calories': null,
    'protein': protein,
    'carbohydrates': null,
    'fat': null,
    'fiber': null,
    'sugar': null,
    'water_intake': waterIntake,
    'notes': '',
    'updated_at': null,
  };
}

Map<String, dynamic> _readinessJson({
  required String readinessDate,
  String recordedAt = '2026-08-08T08:00:00+00:00',
  double? sleepDurationSeconds,
  double? restingHeartRate,
  double? heartRateVariability,
}) {
  return <String, dynamic>{
    'readiness_id': 'r1',
    'user_id': 'u1',
    'readiness_date': readinessDate,
    'recorded_at': recordedAt,
    'sleep_duration_seconds': sleepDurationSeconds,
    'resting_heart_rate': restingHeartRate,
    'heart_rate_variability': heartRateVariability,
    'source': null,
    'notes': '',
    'updated_at': null,
  };
}

void main() {
  group('fetchHome', () {
    test('maps real GET /api/v1/progress list, newest first', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        FakeResponse(
          body: <Map<String, dynamic>>[
            _progressJson(id: 'p-old', progressDate: '2026-07-01', bodyWeight: 82.0),
            _progressJson(id: 'p-new', progressDate: '2026-08-08', bodyWeight: 80.5),
          ],
        ),
        const FakeResponse(body: <Map<String, dynamic>>[]),
        const FakeResponse(body: <Map<String, dynamic>>[]),
      ]);
      final ApiProgressRepository repo = ApiProgressRepository(_clientWith(adapter));

      final ProgressHomeViewState state = await repo.fetchHome();

      expect(state.measurements.length, 2);
      expect(state.measurements.first.progressId, 'p-new');
      expect(state.hasLoggedAnyMeasurementEver, isTrue);
      expect(state.isOffline, isFalse);
      expect(state.lastLogWarnings, isEmpty);

      final List<RequestOptions> sent = adapter.requests;
      expect(sent[0].path, contains('/api/v1/progress'));
      expect(sent[1].path, contains('/api/v1/nutrition'));
      expect(sent[2].path, contains('/api/v1/readiness'));
    });

    test('aggregates a real 7-day nutrition window from the unfiltered list', () async {
      final DateTime today = DateTime.now();
      final String todayKey = apiDateString(today);
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(body: <Map<String, dynamic>>[]),
        FakeResponse(
          body: <Map<String, dynamic>>[
            _nutritionJson(nutritionDate: todayKey, protein: 90, waterIntake: 500),
            _nutritionJson(nutritionDate: todayKey, protein: 40, waterIntake: 300),
          ],
        ),
        const FakeResponse(body: <Map<String, dynamic>>[]),
      ]);
      final ApiProgressRepository repo = ApiProgressRepository(_clientWith(adapter));

      final ProgressHomeViewState state = await repo.fetchHome();

      expect(state.nutritionWeek.length, 7);
      final NutritionDayTotal todayTotal = state.nutritionWeek.last;
      expect(todayTotal.hasAnyEntry, isTrue);
      expect(todayTotal.proteinGrams, 130);
      expect(todayTotal.waterMl, 800);
    });

    test('aggregates readiness by taking the latest-recorded entry per day', () async {
      final DateTime today = DateTime.now();
      final String todayKey = apiDateString(today);
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(body: <Map<String, dynamic>>[]),
        const FakeResponse(body: <Map<String, dynamic>>[]),
        FakeResponse(
          body: <Map<String, dynamic>>[
            _readinessJson(
              readinessDate: todayKey,
              recordedAt: '2026-08-08T06:00:00+00:00',
              sleepDurationSeconds: 6 * 3600,
              restingHeartRate: 58,
            ),
            _readinessJson(
              readinessDate: todayKey,
              recordedAt: '2026-08-08T09:00:00+00:00',
              sleepDurationSeconds: 7.5 * 3600,
              restingHeartRate: 54,
            ),
          ],
        ),
      ]);
      final ApiProgressRepository repo = ApiProgressRepository(_clientWith(adapter));

      final ProgressHomeViewState state = await repo.fetchHome();

      final ReadinessDayEntry todayEntry = state.readinessWeek.last;
      expect(todayEntry.hasAnyEntry, isTrue);
      expect(todayEntry.sleepHours, 7.5);
      expect(todayEntry.restingHeartRate, 54);
    });

    test('zero measurements has never logged any measurement', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(body: <Map<String, dynamic>>[]),
        const FakeResponse(body: <Map<String, dynamic>>[]),
        const FakeResponse(body: <Map<String, dynamic>>[]),
      ]);
      final ApiProgressRepository repo = ApiProgressRepository(_clientWith(adapter));

      final ProgressHomeViewState state = await repo.fetchHome();

      expect(state.hasLoggedAnyMeasurementEver, isFalse);
      expect(state.measurements, isEmpty);
    });

    test('a network failure propagates as ApiException', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(throwConnectionError: true),
      ]);
      final ApiProgressRepository repo = ApiProgressRepository(_clientWith(adapter));

      expect(repo.fetchHome(), throwsA(isA<ApiException>()));
    });
  });

  group('logMeasurement', () {
    test('posts hardcoded unit/source plus only the submitted fields, and returns real warnings',
        () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        FakeResponse(
          statusCode: 201,
          body: <String, dynamic>{
            'id': 'new-progress-id',
            'warnings': <String>[
              '[warning] Fewer than 3 check-ins in the last 30 days — trend confidence is low.',
            ],
          },
        ),
      ]);
      final ApiProgressRepository repo = ApiProgressRepository(_clientWith(adapter));

      final ProgressLogResult result = await repo.logMeasurement(
        date: DateTime(2026, 8, 8),
        bodyWeight: 79.5,
        notes: 'Morning weigh-in',
      );

      expect(result.warnings, <String>[
        '[warning] Fewer than 3 check-ins in the last 30 days — trend confidence is low.',
      ]);
      expect(result.entry.progressId, 'new-progress-id');
      expect(result.entry.bodyWeight, 79.5);
      expect(result.entry.notes, 'Morning weigh-in');
      expect(result.entry.unit, 'metric');
      expect(result.entry.source, 'manual');

      final RequestOptions sent = adapter.requests.single;
      expect(sent.path, contains('/api/v1/progress'));
      expect(sent.method, 'POST');
      final Map<String, dynamic> body = sent.data as Map<String, dynamic>;
      expect(body['progress_date'], apiDateString(DateTime(2026, 8, 8)));
      expect(body['unit'], 'metric');
      expect(body['source'], 'manual');
      expect(body['body_weight'], 79.5);
      expect(body['notes'], 'Morning weigh-in');
      expect(body.containsKey('waist'), isFalse);
    });

    test('an empty warnings list on a clean log is not an error', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(
          statusCode: 201,
          body: <String, dynamic>{'id': 'p-clean', 'warnings': <String>[]},
        ),
      ]);
      final ApiProgressRepository repo = ApiProgressRepository(_clientWith(adapter));

      final ProgressLogResult result = await repo.logMeasurement(date: DateTime(2026, 8, 8));

      expect(result.warnings, isEmpty);
    });

    test('a validation failure (real 400) propagates as ApiException', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        FakeResponse(statusCode: 400, body: <String, dynamic>{'detail': 'invalid body_weight'}),
      ]);
      final ApiProgressRepository repo = ApiProgressRepository(_clientWith(adapter));

      expect(repo.logMeasurement(date: DateTime(2026, 8, 8)), throwsA(isA<ApiException>()));
    });
  });
}
