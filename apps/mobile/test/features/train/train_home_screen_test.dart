import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/app.dart';
import 'package:gym_companion_mobile/design/design.dart';
import 'package:gym_companion_mobile/features/today/application/today_controller.dart';
import 'package:gym_companion_mobile/features/today/infrastructure/mock_today_repository.dart';
import 'package:gym_companion_mobile/features/train/application/train_controller.dart';
import 'package:gym_companion_mobile/features/train/domain/train_models.dart';
import 'package:gym_companion_mobile/shared/domain/session_tier.dart';

/// A controllable fake — mirrors `_FakeTodayRepository`'s own reasoning
/// (`today_screen_test.dart`): [fetchHome] resolves only once [complete]
/// is called, so a test can observe the loading state before resolving.
/// Every other method throws [UnimplementedError] — Train Home's own
/// tests never call them; a test that did would fail loudly instead of
/// silently returning a stub value that could hide a real bug.
class _FakeTrainRepository implements TrainRepository {
  _FakeTrainRepository(this.next);

  final TrainHomeViewState next;
  final Completer<TrainHomeViewState> _completer = Completer<TrainHomeViewState>();

  void complete() {
    if (!_completer.isCompleted) {
      _completer.complete(next);
    }
  }

  void completeWithError() {
    if (!_completer.isCompleted) {
      _completer.completeError(StateError('fetch failed'));
    }
  }

  @override
  Future<TrainHomeViewState> fetchHome() => _completer.future;

  @override
  Future<TrainWorkout> fetchWorkout(String workoutId) => throw UnimplementedError();

  @override
  Future<TrainSession> startSession(String workoutId, {required SessionTier tier}) =>
      throw UnimplementedError();

  @override
  Future<TrainSession> fetchSession(String sessionId) => throw UnimplementedError();

  @override
  Future<TrainSession> logSet(
    String sessionId, {
    required String exerciseId,
    required String exerciseName,
    required int setNumber,
    required double weight,
    required int reps,
    required int rpe,
  }) =>
      throw UnimplementedError();

  @override
  Future<TrainSession> completeSet(
    String sessionId, {
    required String performanceId,
    required int setNumber,
  }) =>
      throw UnimplementedError();

  @override
  Future<TrainSession> completeSession(
    String sessionId, {
    required double durationSeconds,
    required double completionPercentage,
    int? rating,
  }) =>
      throw UnimplementedError();
}

TrainWorkout _workout(String id, String name) {
  return TrainWorkout(
    workoutId: id,
    name: name,
    plannedDate: DateTime(2026, 8, 6),
    status: WorkoutStatus.planned,
  );
}

TrainSession _session(String id, String workoutName, SessionStatus status) {
  return TrainSession(
    sessionId: id,
    workoutId: 'workout-$id',
    workoutName: workoutName,
    status: status,
    sessionDate: DateTime(2026, 8, 4),
    exercisePerformances: const <TrainExercisePerformance>[],
    completionPercentage: 100,
  );
}

Future<void> _pumpTrain(WidgetTester tester, TrainHomeViewState state) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: <Override>[
        todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
        trainRepositoryProvider
            .overrideWithValue(_FakeTrainRepository(state)..complete()),
      ],
      child: const GymCompanionApp(),
    ),
  );
  await tester.pumpAndSettle();
  await tester.tap(find.text('Train').last);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('shows a skeleton, never a spinner, while the first fetch is pending', (
    tester,
  ) async {
    final _FakeTrainRepository repo = _FakeTrainRepository(
      const TrainHomeViewState(status: TrainHomeStatus.ready),
    );
    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
          todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
          trainRepositoryProvider.overrideWithValue(repo),
        ],
        child: const GymCompanionApp(),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Train').last);
    await tester.pump();

    expect(find.byType(AppSkeletonBox), findsWidgets);
    expect(find.byType(CircularProgressIndicator), findsNothing);

    repo.complete();
    await tester.pumpAndSettle();
  });

  testWidgets("this week's workouts render as workout cards", (tester) async {
    await _pumpTrain(
      tester,
      TrainHomeViewState(
        status: TrainHomeStatus.ready,
        thisWeek: <TrainWorkout>[_workout('w1', 'Upper Body Strength')],
      ),
    );

    expect(find.text('Upper Body Strength'), findsOneWidget);
  });

  testWidgets('switching to the History tab shows past sessions', (tester) async {
    await _pumpTrain(
      tester,
      TrainHomeViewState(
        status: TrainHomeStatus.ready,
        thisWeek: <TrainWorkout>[_workout('w1', 'Upper Body Strength')],
        history: <TrainSession>[_session('s1', 'Lower Body Power', SessionStatus.completed)],
      ),
    );

    expect(find.text('Lower Body Power'), findsNothing);
    await tester.tap(find.text('History'));
    await tester.pumpAndSettle();
    expect(find.text('Lower Body Power'), findsOneWidget);
    expect(find.text('Completed'), findsOneWidget);
  });

  testWidgets('switching to the Library tab shows the not-connected placeholder, '
      'not fake exercise data', (tester) async {
    await _pumpTrain(tester, const TrainHomeViewState(status: TrainHomeStatus.ready));

    await tester.tap(find.text('Library'));
    await tester.pumpAndSettle();

    expect(find.text('Exercise library not connected yet'), findsOneWidget);
  });

  testWidgets('no planned workouts shows the empty state, not a workout card', (
    tester,
  ) async {
    await _pumpTrain(tester, const TrainHomeViewState(status: TrainHomeStatus.ready));

    expect(find.text('Nothing planned this week'), findsOneWidget);
  });

  testWidgets('no active plan shows the onboarding empty state for the whole tab', (
    tester,
  ) async {
    await _pumpTrain(
      tester,
      const TrainHomeViewState(status: TrainHomeStatus.ready, hasActivePlan: false),
    );

    expect(find.text('No training plan yet'), findsOneWidget);
  });

  testWidgets('a genuine page fetch failure offers retry, not a silent blank screen', (
    tester,
  ) async {
    final _FakeTrainRepository repo = _FakeTrainRepository(
      const TrainHomeViewState(status: TrainHomeStatus.ready),
    );
    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
          todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
          trainRepositoryProvider.overrideWithValue(repo),
        ],
        child: const GymCompanionApp(),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Train').last);
    repo.completeWithError();
    await tester.pumpAndSettle();

    expect(find.text("Train couldn't be loaded."), findsOneWidget);
    expect(find.text('Try again'), findsOneWidget);
  });

  testWidgets('offline shows a small inline indicator, not a banner', (tester) async {
    await _pumpTrain(
      tester,
      const TrainHomeViewState(status: TrainHomeStatus.ready, isOffline: true),
    );

    expect(find.textContaining('Offline'), findsOneWidget);
  });
}
