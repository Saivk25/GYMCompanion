import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/app.dart';
import 'package:gym_companion_mobile/design/design.dart';
import 'package:gym_companion_mobile/features/fuel/application/fuel_controller.dart';
import 'package:gym_companion_mobile/features/fuel/infrastructure/mock_fuel_repository.dart';
import 'package:gym_companion_mobile/features/progress/application/progress_controller.dart';
import 'package:gym_companion_mobile/features/progress/domain/progress_models.dart';
import 'package:gym_companion_mobile/features/today/application/today_controller.dart';
import 'package:gym_companion_mobile/features/today/infrastructure/mock_today_repository.dart';
import 'package:gym_companion_mobile/features/train/application/train_controller.dart';
import 'package:gym_companion_mobile/features/train/infrastructure/mock_train_repository.dart';

/// A controllable fake — mirrors `_FakeFuelRepository`'s own reasoning
/// (`fuel_home_screen_test.dart`): [fetchHome] resolves only once
/// [complete] is called. [logMeasurement] throws — Progress Home's own
/// tests never call it; the logging flow itself is covered end-to-end in
/// `log_measurement_flow_test.dart` against the real
/// `MockProgressRepository`.
class _FakeProgressRepository implements ProgressRepository {
  _FakeProgressRepository(this.next);

  final ProgressHomeViewState next;
  final Completer<ProgressHomeViewState> _completer = Completer<ProgressHomeViewState>();

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
  Future<ProgressHomeViewState> fetchHome() => _completer.future;

  @override
  Future<ProgressEntry> logMeasurement({
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
  }) =>
      throw UnimplementedError();
}

Future<void> _pumpProgress(WidgetTester tester, ProgressHomeViewState state) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: <Override>[
        todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
        trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
        fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
        progressRepositoryProvider.overrideWithValue(_FakeProgressRepository(state)..complete()),
      ],
      child: const GymCompanionApp(),
    ),
  );
  await tester.pumpAndSettle();
  await tester.tap(find.text('Progress').last);
  await tester.pumpAndSettle();
}

NutritionDayTotal _nutritionDay(int daysAgo, {bool hasEntry = true, double protein = 140}) {
  return NutritionDayTotal(
    date: DateTime.now().subtract(Duration(days: daysAgo)),
    proteinGrams: protein,
    waterMl: 2000,
    hasAnyEntry: hasEntry,
  );
}

List<NutritionDayTotal> _fullNutritionWeek() =>
    List<NutritionDayTotal>.generate(7, (int i) => _nutritionDay(6 - i));

List<NutritionDayTotal> _emptyNutritionWeek() =>
    List<NutritionDayTotal>.generate(7, (int i) => _nutritionDay(6 - i, hasEntry: false, protein: 0));

void main() {
  testWidgets('shows a skeleton, never a spinner, while the first fetch is pending', (
    tester,
  ) async {
    final _FakeProgressRepository repo = _FakeProgressRepository(
      ProgressHomeViewState(asOf: DateTime.now()),
    );
    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
          todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
          trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
          fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
          progressRepositoryProvider.overrideWithValue(repo),
        ],
        child: const GymCompanionApp(),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Progress').last);
    await tester.pump();

    expect(find.byType(AppSkeletonBox), findsWidgets);
    expect(find.byType(CircularProgressIndicator), findsNothing);

    repo.complete();
    await tester.pumpAndSettle();
  });

  testWidgets('Nutrition is the default segment and renders a real protein trend', (
    tester,
  ) async {
    await _pumpProgress(
      tester,
      ProgressHomeViewState(asOf: DateTime.now(), nutritionWeek: _fullNutritionWeek()),
    );

    expect(find.text('Protein, last 7 days'), findsOneWidget);
    expect(find.text('Weekly pattern'), findsOneWidget);
  });

  testWidgets('Nutrition shows "building your first trend" with no logged history', (
    tester,
  ) async {
    await _pumpProgress(
      tester,
      ProgressHomeViewState(asOf: DateTime.now(), nutritionWeek: _emptyNutritionWeek()),
    );

    expect(find.text('Building your first trend'), findsOneWidget);
  });

  testWidgets('the Workout segment is an honest, reachable placeholder', (tester) async {
    await _pumpProgress(tester, ProgressHomeViewState(asOf: DateTime.now()));

    await tester.tap(find.text('Workout'));
    await tester.pumpAndSettle();

    expect(find.text('Workout dashboard not connected yet'), findsOneWidget);
  });

  testWidgets('the Reports segment is an honest, reachable placeholder', (tester) async {
    await _pumpProgress(tester, ProgressHomeViewState(asOf: DateTime.now()));

    await tester.tap(find.text('Reports'));
    await tester.pumpAndSettle();

    expect(find.text('Reports not connected yet'), findsOneWidget);
  });

  testWidgets('Transformation prompts a first baseline capture with no measurements', (
    tester,
  ) async {
    await _pumpProgress(
      tester,
      ProgressHomeViewState(asOf: DateTime.now(), hasLoggedAnyMeasurementEver: false),
    );

    await tester.tap(find.text('Transformation'));
    await tester.pumpAndSettle();

    expect(find.text('Log your first check-in'), findsOneWidget);
  });

  testWidgets('Transformation shows the latest real weight once logged', (tester) async {
    await _pumpProgress(
      tester,
      ProgressHomeViewState(
        asOf: DateTime.now(),
        measurements: <ProgressEntry>[
          ProgressEntry(
            progressId: 'p1',
            progressDate: DateTime.now(),
            recordedAt: DateTime.now(),
            bodyWeight: 79.4,
          ),
        ],
      ),
    );

    await tester.tap(find.text('Transformation'));
    await tester.pumpAndSettle();

    expect(find.text('79.4 kg'), findsOneWidget);
  });

  testWidgets('a genuine page fetch failure offers retry, not a silent blank screen', (
    tester,
  ) async {
    final _FakeProgressRepository repo = _FakeProgressRepository(
      ProgressHomeViewState(asOf: DateTime.now()),
    );
    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
          todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
          trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
          fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
          progressRepositoryProvider.overrideWithValue(repo),
        ],
        child: const GymCompanionApp(),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Progress').last);
    repo.completeWithError();
    await tester.pumpAndSettle();

    expect(find.text("Progress couldn't be loaded."), findsOneWidget);
    expect(find.text('Try again'), findsOneWidget);
  });

  testWidgets('offline shows a small inline indicator, not a banner', (tester) async {
    await _pumpProgress(tester, ProgressHomeViewState(asOf: DateTime.now(), isOffline: true));

    expect(find.textContaining('Offline'), findsOneWidget);
  });
}
