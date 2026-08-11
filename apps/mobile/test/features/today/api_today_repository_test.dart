import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/core/cache/cache.dart';
import 'package:gym_companion_mobile/core/mapping/mapping.dart';
import 'package:gym_companion_mobile/core/network/network.dart';
import 'package:gym_companion_mobile/features/today/domain/today_models.dart';
import 'package:gym_companion_mobile/features/today/infrastructure/api_today_repository.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../core/network/fakes/fake_http_client_adapter.dart';

/// [ApiTodayRepository] against the same hand-written [FakeHttpClientAdapter]
/// `test/core/network/`'s own tests already established — no new test
/// dependency, and this proves the repository against the real
/// [ApiClient]/[Dio] pipeline (URL construction, JSON decoding), not a
/// hand-rolled repository-level fake that would only prove this file
/// agrees with itself.
ApiClient _clientWith(FakeHttpClientAdapter adapter) {
  final Dio dio = Dio(BaseOptions(baseUrl: 'http://test'));
  dio.httpClientAdapter = adapter;
  return ApiClient(dio: dio);
}

/// A fresh, empty [LocalCache] per call — backed by a real (mocked)
/// [SharedPreferences] instance (`docs/adr/0052-offline-caching.md`),
/// not a hand-rolled fake: [LocalCache] is a thin concrete wrapper, not
/// an interface, so there is nothing to fake here, the same reasoning
/// `test/features/auth/auth_controller_test.dart` already established
/// for its own [LocalCache] test usage.
Future<LocalCache> _freshCache() async {
  SharedPreferences.setMockInitialValues(<String, Object>{});
  return LocalCache(await SharedPreferences.getInstance());
}

Future<ApiTodayRepository> _repoWith(
  FakeHttpClientAdapter adapter, {
  LocalCache? cache,
}) async {
  return ApiTodayRepository(_clientWith(adapter), cache ?? await _freshCache());
}

Map<String, dynamic> _workoutJson({
  String id = 'w1',
  String status = 'planned',
  String name = 'Upper Body Strength',
  required String plannedDate,
  String? goal,
  String? notes,
}) {
  return <String, dynamic>{
    'workout_id': id,
    'user_id': 'u1',
    'status': status,
    'name': name,
    'planned_date': plannedDate,
    'planned_at': '2026-08-01T10:00:00+00:00',
    'goal': goal,
    'notes': notes,
    'duration_seconds': null,
    'started_at': null,
    'completed_at': null,
    'cancelled_at': null,
  };
}

Map<String, dynamic> _readinessJson({String id = 'r1', required String readinessDate}) {
  return <String, dynamic>{
    'readiness_id': id,
    'user_id': 'u1',
    'readiness_date': readinessDate,
    'recorded_at': '2026-08-01T08:00:00+00:00',
    'source': null,
    'sleep_duration_seconds': null,
    'sleep_quality': null,
    'energy_level': null,
    'stress_level': null,
    'soreness_level': null,
    'resting_heart_rate': null,
    'heart_rate_variability': null,
    'notes': '',
    'updated_at': null,
  };
}

FakeHttpClientAdapter _adapterFor({
  required List<Map<String, dynamic>> workouts,
  required List<Map<String, dynamic>> readiness,
}) {
  return FakeHttpClientAdapter.responding((RequestOptions options, int callIndex) {
    if (options.path.contains('/workouts')) {
      return FakeResponse(body: workouts);
    }
    if (options.path.contains('/readiness')) {
      return FakeResponse(body: readiness);
    }
    throw StateError('Unexpected path in ApiTodayRepository test: ${options.path}');
  });
}

void main() {
  final String today = apiDateString(DateTime.now());
  final String yesterday = apiDateString(DateTime.now().subtract(const Duration(days: 1)));

  test('a planned workout for today maps to a ready session with real fields', () async {
    final ApiTodayRepository repo = await _repoWith(
      _adapterFor(
        workouts: <Map<String, dynamic>>[
          _workoutJson(
            plannedDate: today,
            status: 'planned',
            name: 'Upper Body Strength',
            goal: 'Build strength',
            notes: 'Focus on form',
          ),
        ],
        readiness: <Map<String, dynamic>>[],
      ),
    );

    final TodayViewState state = await repo.fetchToday();

    expect(state.hasActivePlan, isTrue);
    expect(state.sessionStatus, SessionCardStatus.ready);
    expect(state.session, isNotNull);
    expect(state.session!.name, 'Upper Body Strength');
    expect(state.session!.goal, 'Build strength');
    expect(state.session!.notes, 'Focus on form');
    expect(state.checkInCompletedToday, isFalse);
    expect(state.readinessBand, ReadinessBand.normal);
    expect(state.streak, isNull);
    expect(state.task, isNull);
    expect(state.isOffline, isFalse);
  });

  test('an in-progress workout for today also maps to a ready session', () async {
    final ApiTodayRepository repo = await _repoWith(
      _adapterFor(
        workouts: <Map<String, dynamic>>[
          _workoutJson(plannedDate: today, status: 'in_progress'),
        ],
        readiness: <Map<String, dynamic>>[],
      ),
    );

    final TodayViewState state = await repo.fetchToday();

    expect(state.sessionStatus, SessionCardStatus.ready);
  });

  test('a completed workout for today maps to a completed session', () async {
    final ApiTodayRepository repo = await _repoWith(
      _adapterFor(
        workouts: <Map<String, dynamic>>[
          _workoutJson(plannedDate: today, status: 'completed'),
        ],
        readiness: <Map<String, dynamic>>[],
      ),
    );

    final TodayViewState state = await repo.fetchToday();

    expect(state.sessionStatus, SessionCardStatus.completed);
    expect(state.session, isNotNull);
  });

  test('a cancelled workout for today is treated as empty, not ready', () async {
    final ApiTodayRepository repo = await _repoWith(
      _adapterFor(
        workouts: <Map<String, dynamic>>[
          _workoutJson(plannedDate: today, status: 'cancelled'),
        ],
        readiness: <Map<String, dynamic>>[],
      ),
    );

    final TodayViewState state = await repo.fetchToday();

    expect(state.sessionStatus, SessionCardStatus.empty);
    expect(state.session, isNull);
    // A cancelled workout is not counted toward "has an active plan"
    // either — it is the only workout in this fixture.
    expect(state.hasActivePlan, isFalse);
  });

  test('no workout for today, but a future one exists, still has an active plan', () async {
    final ApiTodayRepository repo = await _repoWith(
      _adapterFor(
        workouts: <Map<String, dynamic>>[
          _workoutJson(plannedDate: '2099-01-01', status: 'planned'),
        ],
        readiness: <Map<String, dynamic>>[],
      ),
    );

    final TodayViewState state = await repo.fetchToday();

    expect(state.hasActivePlan, isTrue);
    expect(state.sessionStatus, SessionCardStatus.empty);
    expect(state.session, isNull);
  });

  test('zero workouts at all has no active plan', () async {
    final ApiTodayRepository repo = await _repoWith(
      _adapterFor(workouts: <Map<String, dynamic>>[], readiness: <Map<String, dynamic>>[]),
    );

    final TodayViewState state = await repo.fetchToday();

    expect(state.hasActivePlan, isFalse);
    expect(state.sessionStatus, SessionCardStatus.empty);
  });

  test('a readiness entry recorded today sets checkInCompletedToday', () async {
    final ApiTodayRepository repo = await _repoWith(
      _adapterFor(
        workouts: <Map<String, dynamic>>[],
        readiness: <Map<String, dynamic>>[
          _readinessJson(readinessDate: yesterday),
          _readinessJson(id: 'r2', readinessDate: today),
        ],
      ),
    );

    final TodayViewState state = await repo.fetchToday();

    expect(state.checkInCompletedToday, isTrue);
  });

  test('a network failure from either endpoint propagates as ApiException '
      'when there is no cached fallback', () async {
    final FakeHttpClientAdapter adapter = FakeHttpClientAdapter.responding(
      (RequestOptions options, int callIndex) =>
          const FakeResponse(throwConnectionError: true),
    );
    final ApiTodayRepository repo = await _repoWith(adapter);

    expect(repo.fetchToday(), throwsA(isA<ApiException>()));
  });

  group('read-through cache (docs/adr/0052-offline-caching.md)', () {
    test('a network failure falls back to a stale cached bundle with isOffline: true', () async {
      final LocalCache cache = await _freshCache();
      await cache.write(
        'today',
        <String, dynamic>{
          'workouts': <Map<String, dynamic>>[
            _workoutJson(plannedDate: today, status: 'planned', name: 'Cached Session'),
          ],
          'readiness': <Map<String, dynamic>>[],
        },
        // Older than `kCacheFreshDuration` (5 minutes) — forces the
        // "try live, fall back to cache" branch rather than the
        // stale-while-revalidate fast path exercised below.
        cachedAt: DateTime.now().subtract(const Duration(hours: 1)),
      );
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter.responding(
        (RequestOptions options, int callIndex) => const FakeResponse(throwConnectionError: true),
      );
      final ApiTodayRepository repo = await _repoWith(adapter, cache: cache);

      final TodayViewState state = await repo.fetchToday();

      expect(state.isOffline, isTrue);
      expect(state.session!.name, 'Cached Session');
    });

    test('a genuine 500 is never masked by a stale cache hit', () async {
      final LocalCache cache = await _freshCache();
      await cache.write(
        'today',
        <String, dynamic>{
          'workouts': <Map<String, dynamic>>[],
          'readiness': <Map<String, dynamic>>[],
        },
        cachedAt: DateTime.now().subtract(const Duration(hours: 1)),
      );
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter.responding(
        (RequestOptions options, int callIndex) =>
            const FakeResponse(statusCode: 500, body: <String, dynamic>{'detail': 'boom'}),
      );
      final ApiTodayRepository repo = await _repoWith(adapter, cache: cache);

      expect(repo.fetchToday(), throwsA(isA<ApiException>()));
    });

    test('a fresh cache entry is served immediately (stale-while-revalidate), '
        'not a blocking second fetch', () async {
      final LocalCache cache = await _freshCache();
      int callCount = 0;
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter.responding((
        RequestOptions options,
        int callIndex,
      ) {
        callCount++;
        if (callCount > 2) {
          // Any call past the first fetchToday()'s own two GETs must be
          // the fire-and-forget background revalidate, never something
          // the *second* fetchToday() call below blocks on awaiting —
          // if it did, this failure would propagate synchronously and
          // fail this test loudly.
          return const FakeResponse(throwConnectionError: true);
        }
        if (options.path.contains('/workouts')) {
          return FakeResponse(
            body: <Map<String, dynamic>>[
              _workoutJson(plannedDate: today, status: 'planned', name: 'Fresh Session'),
            ],
          );
        }
        return const FakeResponse(body: <Map<String, dynamic>>[]);
      });
      final ApiTodayRepository repo = await _repoWith(adapter, cache: cache);

      final TodayViewState first = await repo.fetchToday();
      expect(first.isOffline, isFalse);
      expect(first.session!.name, 'Fresh Session');

      final TodayViewState second = await repo.fetchToday();
      expect(second.isOffline, isFalse);
      expect(second.session!.name, 'Fresh Session');
    });
  });
}
