import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/app.dart';
import 'package:gym_companion_mobile/design/design.dart';
import 'package:gym_companion_mobile/features/coach/application/coach_controller.dart';
import 'package:gym_companion_mobile/features/coach/infrastructure/mock_coach_repository.dart';
import 'package:gym_companion_mobile/features/fuel/application/fuel_controller.dart';
import 'package:gym_companion_mobile/features/fuel/domain/fuel_models.dart';
import 'package:gym_companion_mobile/features/today/application/today_controller.dart';
import 'package:gym_companion_mobile/features/today/infrastructure/mock_today_repository.dart';
import 'package:gym_companion_mobile/features/train/application/train_controller.dart';
import 'package:gym_companion_mobile/features/train/infrastructure/mock_train_repository.dart';
import 'package:gym_companion_mobile/shared/application/coach_signal_log.dart';

/// A controllable fake — mirrors `_FakeTrainRepository`'s own reasoning
/// (`train_home_screen_test.dart`): [fetchHome] resolves only once
/// [complete] is called. [logMeal]/[logWater] throw — Fuel Home's own
/// tests never call them; the logging flow itself is covered end-to-end
/// in `log_meal_flow_test.dart` against the real `MockFuelRepository`.
class _FakeFuelRepository implements FuelRepository {
  _FakeFuelRepository(this.next);

  final FuelHomeViewState next;
  final Completer<FuelHomeViewState> _completer = Completer<FuelHomeViewState>();

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
  Future<FuelHomeViewState> fetchHome() => _completer.future;

  @override
  Future<FuelEntry> logMeal({
    required DateTime date,
    MealType? mealType,
    double? calories,
    double? protein,
    double? carbohydrates,
    double? fat,
    double? fiber,
    double? sugar,
    String? notes,
  }) =>
      throw UnimplementedError();

  @override
  Future<FuelEntry> logWater({required DateTime date, required double amountMl}) =>
      throw UnimplementedError();
}

FuelEntry _meal(String id, {MealType type = MealType.breakfast}) {
  return FuelEntry(
    nutritionId: id,
    nutritionDate: DateTime.now(),
    recordedAt: DateTime.now(),
    mealType: type,
    calories: 400,
    protein: 25,
  );
}

Future<void> _pumpFuel(WidgetTester tester, FuelHomeViewState state) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: <Override>[
        todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
        trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
        fuelRepositoryProvider.overrideWithValue(_FakeFuelRepository(state)..complete()),
        coachRepositoryProvider.overrideWith(
          (ref) => MockCoachRepository(() => ref.read(coachSignalLogProvider)),
        ),
      ],
      child: const GymCompanionApp(),
    ),
  );
  await tester.pumpAndSettle();
  await tester.tap(find.text('Fuel').last);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('shows a skeleton, never a spinner, while the first fetch is pending', (
    tester,
  ) async {
    final _FakeFuelRepository repo = _FakeFuelRepository(
      FuelHomeViewState(date: DateTime.now()),
    );
    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
          todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
          trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
          fuelRepositoryProvider.overrideWithValue(repo),
          coachRepositoryProvider.overrideWith(
            (ref) => MockCoachRepository(() => ref.read(coachSignalLogProvider)),
          ),
        ],
        child: const GymCompanionApp(),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Fuel').last);
    await tester.pump();

    expect(find.byType(AppSkeletonBox), findsWidgets);
    expect(find.byType(CircularProgressIndicator), findsNothing);

    repo.complete();
    await tester.pumpAndSettle();
  });

  testWidgets("today's logged meals render as list rows", (tester) async {
    await _pumpFuel(
      tester,
      FuelHomeViewState(
        date: DateTime.now(),
        todayEntries: <FuelEntry>[_meal('m1', type: MealType.breakfast)],
      ),
    );

    expect(find.text('Breakfast'), findsOneWidget);
  });

  testWidgets('a brand-new user sees the three-methods explainer, not a bare '
      'empty list', (tester) async {
    await _pumpFuel(
      tester,
      FuelHomeViewState(date: DateTime.now(), hasLoggedAnyMealEver: false),
    );

    expect(find.text('Three ways to log a meal'), findsOneWidget);
  });

  testWidgets('a returning user with nothing logged today sees a quieter '
      'empty state, not the first-use explainer', (tester) async {
    await _pumpFuel(
      tester,
      FuelHomeViewState(date: DateTime.now(), hasLoggedAnyMealEver: true),
    );

    expect(find.text('Nothing logged today yet'), findsOneWidget);
    expect(find.text('Three ways to log a meal'), findsNothing);
  });

  testWidgets('hydration total and target render together, non-alarming', (
    tester,
  ) async {
    await _pumpFuel(
      tester,
      FuelHomeViewState(
        date: DateTime.now(),
        todayEntries: <FuelEntry>[
          FuelEntry(
            nutritionId: 'w1',
            nutritionDate: DateTime.now(),
            recordedAt: DateTime.now(),
            waterIntake: 500,
          ),
        ],
      ),
    );

    expect(find.text('500 / 2000 ml'), findsOneWidget);
  });

  testWidgets('the weekly pattern line renders when present', (tester) async {
    await _pumpFuel(
      tester,
      FuelHomeViewState(
        date: DateTime.now(),
        hasLoggedAnyMealEver: true,
        proteinConsistencyLabel: '4 of the last 7 days on target',
      ),
    );

    expect(find.text('4 of the last 7 days on target'), findsOneWidget);
  });

  testWidgets('a genuine page fetch failure offers retry, not a silent blank '
      'screen', (tester) async {
    final _FakeFuelRepository repo = _FakeFuelRepository(
      FuelHomeViewState(date: DateTime.now()),
    );
    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
          todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
          trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
          fuelRepositoryProvider.overrideWithValue(repo),
          coachRepositoryProvider.overrideWith(
            (ref) => MockCoachRepository(() => ref.read(coachSignalLogProvider)),
          ),
        ],
        child: const GymCompanionApp(),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Fuel').last);
    repo.completeWithError();
    await tester.pumpAndSettle();

    expect(find.text("Fuel couldn't be loaded."), findsOneWidget);
    expect(find.text('Try again'), findsOneWidget);
  });

  testWidgets('offline shows a small inline indicator, not a banner', (tester) async {
    await _pumpFuel(
      tester,
      FuelHomeViewState(date: DateTime.now(), isOffline: true),
    );

    expect(find.textContaining('Offline'), findsOneWidget);
  });
}
