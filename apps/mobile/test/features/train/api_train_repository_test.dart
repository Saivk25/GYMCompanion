import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/core/mapping/mapping.dart';
import 'package:gym_companion_mobile/core/network/network.dart';
import 'package:gym_companion_mobile/features/train/application/train_controller.dart';
import 'package:gym_companion_mobile/features/train/domain/train_models.dart';
import 'package:gym_companion_mobile/features/train/infrastructure/api_train_repository.dart';
import 'package:gym_companion_mobile/shared/domain/session_tier.dart';

import '../../core/network/fakes/fake_http_client_adapter.dart';

/// [ApiTrainRepository] against the same hand-written
/// [FakeHttpClientAdapter] `ApiTodayRepository`'s and
/// `ApiReadinessRepository`'s own tests already established — see that
/// file's own doc comment for why (proves the real `ApiClient`/`Dio`
/// pipeline, not a hand-rolled repository-level fake).
ApiClient _clientWith(HttpClientAdapter adapter) {
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
  double? durationSeconds,
}) {
  return <String, dynamic>{
    'workout_id': id,
    'user_id': 'u1',
    'status': status,
    'name': name,
    'planned_date': plannedDate,
    'planned_at': '2026-08-01T08:00:00+00:00',
    'goal': goal,
    'notes': notes,
    'duration_seconds': durationSeconds,
    'started_at': null,
    'completed_at': null,
    'cancelled_at': null,
  };
}

Map<String, dynamic> _sessionJson({
  String id = 's1',
  String workoutId = 'w1',
  String status = 'active',
  String sessionDate = '2026-08-08',
  List<Map<String, dynamic>>? performances,
}) {
  return <String, dynamic>{
    'session_id': id,
    'workout_id': workoutId,
    'user_id': 'u1',
    'status': status,
    'session_date': sessionDate,
    'planned_at': '2026-08-08T08:00:00+00:00',
    'notes': '',
    'duration_seconds': null,
    'completion_percentage': null,
    'rating': null,
    'started_at': null,
    'completed_at': null,
    'abandoned_at': null,
    'exercise_performances': performances ?? <Map<String, dynamic>>[],
  };
}

Map<String, dynamic> _performanceJson({
  String performanceId = 'perf1',
  String exerciseId = 'ex1',
  List<Map<String, dynamic>>? sets,
}) {
  return <String, dynamic>{
    'performance_id': performanceId,
    'exercise_id': exerciseId,
    'notes': '',
    'sets': sets ?? <Map<String, dynamic>>[],
  };
}

Map<String, dynamic> _setJson({
  int setNumber = 1,
  double weight = 60,
  int reps = 8,
  int rpe = 7,
  bool completed = true,
}) {
  return <String, dynamic>{
    'set_number': setNumber,
    'weight': weight,
    'reps': reps,
    'rpe': rpe,
    'completed': completed,
  };
}

void main() {
  group('fetchHome', () {
    test('maps a real GET /api/v1/workouts list, filtering thisWeek and always emptying history',
        () async {
      final DateTime today = DateTime.now();
      final String todayKey = apiDateString(today);
      final String farFuture = apiDateString(today.add(const Duration(days: 30)));

      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        FakeResponse(
          body: <Map<String, dynamic>>[
            _workoutJson(id: 'w-today', status: 'planned', plannedDate: todayKey),
            _workoutJson(id: 'w-far', status: 'planned', plannedDate: farFuture),
            _workoutJson(id: 'w-done', status: 'completed', plannedDate: todayKey),
            _workoutJson(id: 'w-cancelled', status: 'cancelled', plannedDate: todayKey),
          ],
        ),
      ]);
      final ApiTrainRepository repo = ApiTrainRepository(_clientWith(adapter));

      final TrainHomeViewState state = await repo.fetchHome();

      expect(state.thisWeek.map((TrainWorkout w) => w.workoutId), <String>['w-today']);
      expect(state.history, isEmpty);
      expect(state.hasActivePlan, isTrue);
      expect(state.isOffline, isFalse);
    });

    test('hasActivePlan is false when every workout is cancelled', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        FakeResponse(
          body: <Map<String, dynamic>>[
            _workoutJson(status: 'cancelled', plannedDate: apiDateString(DateTime.now())),
          ],
        ),
      ]);
      final ApiTrainRepository repo = ApiTrainRepository(_clientWith(adapter));

      final TrainHomeViewState state = await repo.fetchHome();

      expect(state.hasActivePlan, isFalse);
    });

    test('a network failure propagates as ApiException', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(throwConnectionError: true),
      ]);
      final ApiTrainRepository repo = ApiTrainRepository(_clientWith(adapter));

      expect(repo.fetchHome(), throwsA(isA<ApiException>()));
    });
  });

  group('fetchWorkout', () {
    test('maps a real GET /api/v1/workouts/{id} to TrainWorkout', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        FakeResponse(
          body: _workoutJson(
            id: 'w1',
            plannedDate: '2026-08-10',
            goal: 'Build pressing strength',
            notes: 'Focus on bar speed.',
          ),
        ),
      ]);
      final ApiTrainRepository repo = ApiTrainRepository(_clientWith(adapter));

      final TrainWorkout workout = await repo.fetchWorkout('w1');

      expect(workout.workoutId, 'w1');
      expect(workout.name, 'Upper Body Strength');
      expect(workout.status, WorkoutStatus.planned);
      expect(workout.goal, 'Build pressing strength');
      expect(workout.notes, 'Focus on bar speed.');
      expect(adapter.requests.single.path, contains('/api/v1/workouts/w1'));
    });
  });

  group('startSession', () {
    test('posts session_date only (never tier), then refetches session + workout', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        FakeResponse(
          statusCode: 201,
          body: <String, dynamic>{'id': 's-new', 'warnings': <String>[]},
        ),
        FakeResponse(body: _sessionJson(id: 's-new', workoutId: 'w1', status: 'active')),
        FakeResponse(body: _workoutJson(id: 'w1', plannedDate: '2026-08-08')),
      ]);
      final ApiTrainRepository repo = ApiTrainRepository(_clientWith(adapter));

      final TrainSession session =
          await repo.startSession('w1', tier: SessionTier.standard);

      expect(session.sessionId, 's-new');
      expect(session.workoutId, 'w1');
      expect(session.workoutName, 'Upper Body Strength');
      expect(session.status, SessionStatus.active);

      final RequestOptions postRequest = adapter.requests[0];
      expect(postRequest.method, 'POST');
      expect(postRequest.path, contains('/api/v1/workouts/w1/sessions'));
      final Map<String, dynamic> body = postRequest.data as Map<String, dynamic>;
      expect(body.keys, <String>['session_date']);
      expect(adapter.requests[1].path, contains('/api/v1/workout-sessions/s-new'));
      expect(adapter.requests[2].path, contains('/api/v1/workouts/w1'));
    });

    test('surfaces real warnings from the mutation as lastMutationWarnings', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        FakeResponse(
          statusCode: 201,
          body: <String, dynamic>{
            'id': 's-new',
            'warnings': <String>['[warning] Example advisory.'],
          },
        ),
        FakeResponse(body: _sessionJson(id: 's-new')),
        FakeResponse(body: _workoutJson()),
      ]);
      final ApiTrainRepository repo = ApiTrainRepository(_clientWith(adapter));

      final TrainSession session = await repo.startSession('w1', tier: SessionTier.min);

      expect(session.lastMutationWarnings, <String>['[warning] Example advisory.']);
    });
  });

  group('fetchSession', () {
    test('maps a real session + resolves workoutName from a second workout fetch', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        FakeResponse(
          body: _sessionJson(
            id: 's1',
            workoutId: 'w1',
            performances: <Map<String, dynamic>>[
              _performanceJson(
                performanceId: 'perf1',
                exerciseId: 'ex1',
                sets: <Map<String, dynamic>>[_setJson(setNumber: 1)],
              ),
            ],
          ),
        ),
        FakeResponse(body: _workoutJson(id: 'w1', name: 'Upper Body Strength', plannedDate: '2026-08-08')),
      ]);
      final ApiTrainRepository repo = ApiTrainRepository(_clientWith(adapter));

      final TrainSession session = await repo.fetchSession('s1');

      expect(session.workoutName, 'Upper Body Strength');
      expect(session.exercisePerformances.single.performanceId, 'perf1');
      // No exercise-catalog endpoint exists — the raw id is the honest
      // fallback name (see `ExercisePerformanceDto`'s own doc comment).
      expect(session.exercisePerformances.single.exerciseName, 'ex1');
      expect(session.exercisePerformances.single.sets.single.setNumber, 1);
      expect(session.lastMutationWarnings, isEmpty);
    });
  });

  group('completeSession', () {
    test('posts duration/completion/rating, then refetches, surfacing real warnings', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        FakeResponse(
          body: <String, dynamic>{
            'id': 's1',
            'warnings': <String>['[advisory] Real training-load advice.'],
          },
        ),
        FakeResponse(body: _sessionJson(id: 's1', workoutId: 'w1', status: 'completed')),
        FakeResponse(body: _workoutJson(id: 'w1', plannedDate: '2026-08-08')),
      ]);
      final ApiTrainRepository repo = ApiTrainRepository(_clientWith(adapter));

      final TrainSession session = await repo.completeSession(
        's1',
        durationSeconds: 2700,
        completionPercentage: 100,
        rating: 4,
      );

      expect(session.status, SessionStatus.completed);
      expect(session.lastMutationWarnings, <String>['[advisory] Real training-load advice.']);

      final Map<String, dynamic> body = adapter.requests[0].data as Map<String, dynamic>;
      expect(body['duration_seconds'], 2700);
      expect(body['completion_percentage'], 100);
      expect(body['rating'], 4);
      expect(adapter.requests[0].path, contains('/api/v1/workout-sessions/s1/complete'));
    });

    test('omits rating from the body when null', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        FakeResponse(body: <String, dynamic>{'id': 's1', 'warnings': <String>[]}),
        FakeResponse(body: _sessionJson(id: 's1')),
        FakeResponse(body: _workoutJson()),
      ]);
      final ApiTrainRepository repo = ApiTrainRepository(_clientWith(adapter));

      await repo.completeSession('s1', durationSeconds: 100, completionPercentage: 50);

      final Map<String, dynamic> body = adapter.requests[0].data as Map<String, dynamic>;
      expect(body.containsKey('rating'), isFalse);
    });
  });

  group('logSet / completeSet — deliberately deferred', () {
    test('logSet throws TrainLoggingUnavailableException before any network call', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[]);
      final ApiTrainRepository repo = ApiTrainRepository(_clientWith(adapter));

      await expectLater(
        repo.logSet(
          's1',
          exerciseId: 'ex1',
          exerciseName: 'Back Squat',
          setNumber: 1,
          weight: 60,
          reps: 8,
          rpe: 7,
        ),
        throwsA(isA<TrainLoggingUnavailableException>()),
      );
      expect(adapter.requests, isEmpty);
    });

    test('completeSet throws TrainLoggingUnavailableException before any network call', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[]);
      final ApiTrainRepository repo = ApiTrainRepository(_clientWith(adapter));

      await expectLater(
        repo.completeSet('s1', performanceId: 'perf1', setNumber: 1),
        throwsA(isA<TrainLoggingUnavailableException>()),
      );
      expect(adapter.requests, isEmpty);
    });
  });
}
