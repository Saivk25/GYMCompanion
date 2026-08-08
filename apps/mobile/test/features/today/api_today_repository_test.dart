import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/core/mapping/mapping.dart';
import 'package:gym_companion_mobile/core/network/network.dart';
import 'package:gym_companion_mobile/features/today/domain/today_models.dart';
import 'package:gym_companion_mobile/features/today/infrastructure/api_today_repository.dart';

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
    final ApiTodayRepository repo = ApiTodayRepository(
      _clientWith(
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
    final ApiTodayRepository repo = ApiTodayRepository(
      _clientWith(
        _adapterFor(
          workouts: <Map<String, dynamic>>[
            _workoutJson(plannedDate: today, status: 'in_progress'),
          ],
          readiness: <Map<String, dynamic>>[],
        ),
      ),
    );

    final TodayViewState state = await repo.fetchToday();

    expect(state.sessionStatus, SessionCardStatus.ready);
  });

  test('a completed workout for today maps to a completed session', () async {
    final ApiTodayRepository repo = ApiTodayRepository(
      _clientWith(
        _adapterFor(
          workouts: <Map<String, dynamic>>[
            _workoutJson(plannedDate: today, status: 'completed'),
          ],
          readiness: <Map<String, dynamic>>[],
        ),
      ),
    );

    final TodayViewState state = await repo.fetchToday();

    expect(state.sessionStatus, SessionCardStatus.completed);
    expect(state.session, isNotNull);
  });

  test('a cancelled workout for today is treated as empty, not ready', () async {
    final ApiTodayRepository repo = ApiTodayRepository(
      _clientWith(
        _adapterFor(
          workouts: <Map<String, dynamic>>[
            _workoutJson(plannedDate: today, status: 'cancelled'),
          ],
          readiness: <Map<String, dynamic>>[],
        ),
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
    final ApiTodayRepository repo = ApiTodayRepository(
      _clientWith(
        _adapterFor(
          workouts: <Map<String, dynamic>>[
            _workoutJson(plannedDate: '2099-01-01', status: 'planned'),
          ],
          readiness: <Map<String, dynamic>>[],
        ),
      ),
    );

    final TodayViewState state = await repo.fetchToday();

    expect(state.hasActivePlan, isTrue);
    expect(state.sessionStatus, SessionCardStatus.empty);
    expect(state.session, isNull);
  });

  test('zero workouts at all has no active plan', () async {
    final ApiTodayRepository repo = ApiTodayRepository(
      _clientWith(
        _adapterFor(workouts: <Map<String, dynamic>>[], readiness: <Map<String, dynamic>>[]),
      ),
    );

    final TodayViewState state = await repo.fetchToday();

    expect(state.hasActivePlan, isFalse);
    expect(state.sessionStatus, SessionCardStatus.empty);
  });

  test("a readiness entry recorded today sets checkInCompletedToday", () async {
    final ApiTodayRepository repo = ApiTodayRepository(
      _clientWith(
        _adapterFor(
          workouts: <Map<String, dynamic>>[],
          readiness: <Map<String, dynamic>>[
            _readinessJson(readinessDate: yesterday),
            _readinessJson(id: 'r2', readinessDate: today),
          ],
        ),
      ),
    );

    final TodayViewState state = await repo.fetchToday();

    expect(state.checkInCompletedToday, isTrue);
  });

  test('a network failure from either endpoint propagates as ApiException', () async {
    final FakeHttpClientAdapter adapter = FakeHttpClientAdapter.responding(
      (RequestOptions options, int callIndex) =>
          const FakeResponse(throwConnectionError: true),
    );
    final ApiTodayRepository repo = ApiTodayRepository(_clientWith(adapter));

    expect(repo.fetchToday(), throwsA(isA<ApiException>()));
  });
}
