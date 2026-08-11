import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/app.dart';
import 'package:gym_companion_mobile/features/coach/application/coach_controller.dart';
import 'package:gym_companion_mobile/features/coach/infrastructure/mock_coach_repository.dart';
import 'package:gym_companion_mobile/features/fuel/application/fuel_controller.dart';
import 'package:gym_companion_mobile/features/fuel/infrastructure/mock_fuel_repository.dart';
import 'package:gym_companion_mobile/features/today/application/today_controller.dart';
import 'package:gym_companion_mobile/features/today/infrastructure/mock_today_repository.dart';
import 'package:gym_companion_mobile/features/train/application/train_controller.dart';
import 'package:gym_companion_mobile/features/train/infrastructure/mock_train_repository.dart';
import 'package:gym_companion_mobile/shared/application/coach_signal_log.dart';
import '../../support/auth_test_overrides.dart';

/// End-to-end through the real router and [MockFuelRepository] — the
/// same reasoning `active_workout_screen_test.dart` gives for doing this
/// rather than a narrower unit test. Unlike Active Workout, no screen
/// here runs a live `Timer.periodic`, so ordinary `pumpAndSettle()` is
/// safe throughout — no bounded-`pump()` workaround needed.
Future<void> _pumpToFuelHome(WidgetTester tester) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: <Override>[
        ...authenticatedTestOverrides(),
        todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
        trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
        fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
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
  testWidgets('logging a meal with manual entry appears in the today list', (
    tester,
  ) async {
    await _pumpToFuelHome(tester);

    await tester.tap(find.text('Log a meal'));
    await tester.pumpAndSettle();

    expect(find.text('Log meal'), findsOneWidget);
    // Disabled until calories is entered.
    final Finder logMealButton = find.widgetWithText(ElevatedButton, 'Log meal');
    expect(tester.widget<ElevatedButton>(logMealButton).onPressed, isNull);

    await tester.enterText(find.widgetWithText(TextField, 'Calories').first, '550');
    await tester.pump();
    expect(tester.widget<ElevatedButton>(logMealButton).onPressed, isNotNull);

    await tester.tap(find.text('Log meal'));
    await tester.pumpAndSettle();

    // Back on Fuel Home, the new meal is visible. 'Fuel' matches both
    // the bottom-nav tab label and Fuel Home's own page heading
    // (fuel_home_screen.dart), so this is findsWidgets, not findsOneWidget.
    expect(find.text('Fuel'), findsWidgets);
    expect(find.textContaining('550 kcal'), findsOneWidget);
  });

  testWidgets('photo and menu capture modes show the honest not-connected '
      'placeholder and offer a path to text entry', (tester) async {
    await _pumpToFuelHome(tester);

    await tester.tap(find.text('Log a meal'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Photo'));
    await tester.pumpAndSettle();

    expect(find.text('Photo capture not connected yet'), findsOneWidget);
    expect(find.text('Use text entry instead'), findsOneWidget);

    await tester.tap(find.text('Use text entry instead'));
    await tester.pumpAndSettle();

    expect(find.text('Meal'), findsOneWidget);
    expect(find.widgetWithText(TextField, 'Calories'), findsOneWidget);
  });

  testWidgets('logging water from the hydration card updates the total', (
    tester,
  ) async {
    await _pumpToFuelHome(tester);

    await tester.tap(find.text('Log water'));
    await tester.pumpAndSettle();

    expect(find.text('Log water'), findsWidgets);
    await tester.tap(find.text('500 ml'));
    await tester.pumpAndSettle();

    // Seed data already includes a 500ml entry — logging another 500ml
    // should bring the visible total to 1000ml.
    expect(find.textContaining('1000 / 2000 ml'), findsOneWidget);
  });

  testWidgets('food search is reachable from Log a meal and discloses it '
      "isn't connected", (tester) async {
    await _pumpToFuelHome(tester);

    await tester.tap(find.text('Log a meal'));
    await tester.pumpAndSettle();

    await tester.tap(find.byTooltip('Search foods'));
    await tester.pumpAndSettle();

    expect(find.text('Food search not connected yet'), findsOneWidget);
  });

  testWidgets('supplements is reachable from Fuel Home and discloses it '
      "isn't connected", (tester) async {
    await _pumpToFuelHome(tester);

    await tester.tap(find.text('Supplements'));
    await tester.pumpAndSettle();

    expect(find.text('Supplement tracking not connected yet'), findsOneWidget);
  });
}
