import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/app.dart';
import 'package:gym_companion_mobile/features/fuel/application/fuel_controller.dart';
import 'package:gym_companion_mobile/features/fuel/infrastructure/mock_fuel_repository.dart';
import 'package:gym_companion_mobile/features/progress/application/progress_controller.dart';
import 'package:gym_companion_mobile/features/progress/infrastructure/mock_progress_repository.dart';
import 'package:gym_companion_mobile/features/today/application/today_controller.dart';
import 'package:gym_companion_mobile/features/today/infrastructure/mock_today_repository.dart';
import 'package:gym_companion_mobile/features/train/application/train_controller.dart';
import 'package:gym_companion_mobile/features/train/infrastructure/mock_train_repository.dart';

/// End-to-end through the real router and [MockProgressRepository] —
/// the same reasoning `log_meal_flow_test.dart` gives for doing this
/// rather than a narrower unit test.
Future<void> _pumpToProgressTransformation(WidgetTester tester) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: <Override>[
        todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
        trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
        fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
        progressRepositoryProvider.overrideWithValue(MockProgressRepository()),
      ],
      child: const GymCompanionApp(),
    ),
  );
  await tester.pumpAndSettle();
  await tester.tap(find.text('Progress').last);
  await tester.pumpAndSettle();
  await tester.tap(find.text('Transformation'));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('logging a measurement updates the latest weight shown', (tester) async {
    await _pumpToProgressTransformation(tester);

    // MockProgressRepository's seeded weekly weights end at 80.8 kg.
    expect(find.text('80.8 kg'), findsOneWidget);

    await tester.tap(find.text('Log measurements'));
    await tester.pumpAndSettle();

    expect(find.text('Log measurements'), findsOneWidget); // the AppBar title
    final Finder submitButton = find.widgetWithText(ElevatedButton, 'Log check-in');
    expect(tester.widget<ElevatedButton>(submitButton).onPressed, isNull);

    await tester.enterText(find.widgetWithText(TextField, 'Weight (kg)'), '77.5');
    await tester.pump();
    expect(tester.widget<ElevatedButton>(submitButton).onPressed, isNotNull);

    await tester.tap(find.text('Log check-in'));
    await tester.pumpAndSettle();

    expect(find.text('77.5 kg'), findsOneWidget);
  });

  testWidgets('tapping the weight chart opens its full trend detail', (tester) async {
    await _pumpToProgressTransformation(tester);

    await tester.tap(find.text('Weight, rolling average'));
    await tester.pumpAndSettle();

    expect(find.text('Weight'), findsWidgets); // AppBar title + list row label
  });

  testWidgets('photo check-in is reachable from Transformation and discloses it '
      "isn't connected", (tester) async {
    await _pumpToProgressTransformation(tester);

    await tester.tap(find.text('New photo check-in'));
    await tester.pumpAndSettle();

    expect(find.text('Photo check-in not connected yet'), findsOneWidget);
  });

  testWidgets('photo comparison is reachable from Transformation and discloses it '
      "isn't connected", (tester) async {
    await _pumpToProgressTransformation(tester);

    await tester.tap(find.text('Compare photos'));
    await tester.pumpAndSettle();

    expect(find.text('Photo comparison not connected yet'), findsOneWidget);
  });

  testWidgets('correlations is reachable from Recovery and discloses it '
      "isn't connected", (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
          todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
          trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
          fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
          progressRepositoryProvider.overrideWithValue(MockProgressRepository()),
        ],
        child: const GymCompanionApp(),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Progress').last);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Recovery'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Correlations'));
    await tester.pumpAndSettle();

    expect(find.text('Correlations not connected yet'), findsOneWidget);
  });
}
