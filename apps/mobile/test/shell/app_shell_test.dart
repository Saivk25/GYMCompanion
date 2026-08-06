import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/app.dart';
import 'package:gym_companion_mobile/features/today/application/today_controller.dart';
import 'package:gym_companion_mobile/features/today/infrastructure/mock_today_repository.dart';

/// Every test in this file overrides [todayRepositoryProvider] with
/// [MockTodayRepository] — the default provider deliberately has no
/// implementation (see its own doc comment) and throws if read
/// unoverridden, precisely so a missing override is caught immediately
/// rather than silently rendering Today's error fallback in every test
/// that boots the full app, which would pass without actually exercising
/// Today's real content.
ProviderScope _appWithMockToday() {
  return ProviderScope(
    overrides: <Override>[
      todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
    ],
    child: const GymCompanionApp(),
  );
}

void main() {
  testWidgets('lands on Today and can navigate to Train via the bottom bar', (
    tester,
  ) async {
    await tester.pumpWidget(_appWithMockToday());
    await tester.pumpAndSettle();

    expect(find.text('Today'), findsWidgets);

    await tester.tap(find.text('Train'));
    await tester.pumpAndSettle();

    expect(find.text('Train'), findsWidgets);
  });

  testWidgets('all five tab destinations are present', (tester) async {
    await tester.pumpWidget(_appWithMockToday());
    await tester.pumpAndSettle();

    for (final label in ['Today', 'Train', 'Fuel', 'Progress', 'Coach']) {
      expect(find.text(label), findsWidgets);
    }
  });

  testWidgets('the quick-add FAB is present on Today and absent elsewhere', (
    tester,
  ) async {
    await tester.pumpWidget(_appWithMockToday());
    await tester.pumpAndSettle();

    expect(find.byType(FloatingActionButton), findsOneWidget);

    await tester.tap(find.text('Train'));
    await tester.pumpAndSettle();

    expect(find.byType(FloatingActionButton), findsNothing);
  });
}
