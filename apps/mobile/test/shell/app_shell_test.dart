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

/// Every test in this file overrides [todayRepositoryProvider],
/// [trainRepositoryProvider], [fuelRepositoryProvider], and
/// [progressRepositoryProvider] with their mock implementations — all
/// four deliberately have no default (see each one's own doc comment)
/// and throw if read unoverridden, precisely so a missing override is
/// caught immediately rather than silently rendering an error fallback
/// in every test that boots the full app, which would pass without
/// actually exercising that tab's real content. Fuel joined this
/// requirement once `FuelHomeScreen` replaced the Fuel tab's placeholder
/// (`docs/adr/0038-fuel-module.md`); Progress joined it the same way
/// once `ProgressHomeScreen` replaced its own placeholder
/// (`docs/adr/0039-progress-module.md`).
ProviderScope _appWithMocks() {
  return ProviderScope(
    overrides: <Override>[
      todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
      trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
      fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
      progressRepositoryProvider.overrideWithValue(MockProgressRepository()),
    ],
    child: const GymCompanionApp(),
  );
}

void main() {
  testWidgets('lands on Today and can navigate to Train via the bottom bar', (
    tester,
  ) async {
    await tester.pumpWidget(_appWithMocks());
    await tester.pumpAndSettle();

    expect(find.text('Today'), findsWidgets);

    await tester.tap(find.text('Train'));
    await tester.pumpAndSettle();

    expect(find.text('Train'), findsWidgets);
  });

  testWidgets('all five tab destinations are present', (tester) async {
    await tester.pumpWidget(_appWithMocks());
    await tester.pumpAndSettle();

    for (final label in ['Today', 'Train', 'Fuel', 'Progress', 'Coach']) {
      expect(find.text(label), findsWidgets);
    }
  });

  testWidgets('the quick-add FAB is present on Today and absent elsewhere', (
    tester,
  ) async {
    await tester.pumpWidget(_appWithMocks());
    await tester.pumpAndSettle();

    expect(find.byType(FloatingActionButton), findsOneWidget);

    await tester.tap(find.text('Train'));
    await tester.pumpAndSettle();

    expect(find.byType(FloatingActionButton), findsNothing);
  });
}
