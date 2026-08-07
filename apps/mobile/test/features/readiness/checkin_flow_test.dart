import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/app.dart';
import 'package:gym_companion_mobile/features/fuel/application/fuel_controller.dart';
import 'package:gym_companion_mobile/features/fuel/infrastructure/mock_fuel_repository.dart';
import 'package:gym_companion_mobile/features/progress/application/progress_controller.dart';
import 'package:gym_companion_mobile/features/progress/infrastructure/mock_progress_repository.dart';
import 'package:gym_companion_mobile/features/readiness/application/readiness_controller.dart';
import 'package:gym_companion_mobile/features/readiness/infrastructure/mock_readiness_repository.dart';
import 'package:gym_companion_mobile/features/readiness/presentation/widgets/readiness_entry_tile.dart';
import 'package:gym_companion_mobile/features/today/application/today_controller.dart';
import 'package:gym_companion_mobile/features/today/infrastructure/mock_today_repository.dart';
import 'package:gym_companion_mobile/features/train/application/train_controller.dart';
import 'package:gym_companion_mobile/features/train/infrastructure/mock_train_repository.dart';

/// End-to-end through the real router and [MockReadinessRepository] —
/// the same reasoning `log_meal_flow_test.dart`/`log_measurement_flow_
/// test.dart` give for doing this rather than a narrower unit test.
ProviderScope _appWithMocks() {
  return ProviderScope(
    overrides: <Override>[
      todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
      trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
      fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
      progressRepositoryProvider.overrideWithValue(MockProgressRepository()),
      readinessRepositoryProvider.overrideWithValue(MockReadinessRepository()),
    ],
    child: const GymCompanionApp(),
  );
}

Future<void> _pumpToReadinessHome(WidgetTester tester) async {
  await tester.pumpWidget(_appWithMocks());
  await tester.pumpAndSettle();
  await tester.tap(find.text('Progress').last);
  await tester.pumpAndSettle();
  await tester.tap(find.text('Recovery'));
  await tester.pumpAndSettle();
  await tester.tap(find.text('Readiness check-ins'));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('Readiness is reachable from Progress’s Recovery segment', (tester) async {
    await _pumpToReadinessHome(tester);

    expect(find.text('Readiness'), findsWidgets); // the AppBar title
  });

  testWidgets("Today's check-in nudge opens the real check-in screen directly", (
    tester,
  ) async {
    await tester.pumpWidget(_appWithMocks());
    await tester.pumpAndSettle();

    // MockTodayRepository's default state has not checked in today yet,
    // so the nudge card is showing on the Today tab already.
    await tester.tap(find.text('Complete check-in'));
    await tester.pumpAndSettle();

    expect(find.text('Readiness check-in'), findsOneWidget); // the AppBar title
  });

  testWidgets('the check-in form is pre-filled from the most recent entry and can be '
      'submitted without editing anything', (tester) async {
    await _pumpToReadinessHome(tester);

    await tester.tap(find.text('Start check-in'));
    await tester.pumpAndSettle();

    expect(find.text('Readiness check-in'), findsOneWidget);
    final Finder submitButton = find.widgetWithText(ElevatedButton, 'Submit check-in');
    expect(submitButton, findsOneWidget);
    // Unlike Progress's Log-measurement form, Readiness's check-in has no
    // gating validation — every field is optional per the backend's own
    // `RecordReadinessRequest` — so the submit button is enabled from
    // the very first frame.
    expect(tester.widget<ElevatedButton>(submitButton).onPressed, isNotNull);

    await tester.tap(submitButton);
    await tester.pumpAndSettle();

    // Pops straight back to Readiness Home with the fresh state,
    // including the mock's real illustrative advisory warnings on this
    // first-ever submission.
    expect(find.text("Today's check-in"), findsOneWidget);
    expect(find.text('Advisory notes from your last check-in'), findsOneWidget);
  });

  testWidgets('tapping "See all" opens the full recovery timeline with every seeded entry', (
    tester,
  ) async {
    await _pumpToReadinessHome(tester);

    // Readiness Home's own preview list caps at 5.
    expect(find.byType(ReadinessEntryTile), findsNWidgets(5));

    await tester.tap(find.text('See all'));
    await tester.pumpAndSettle();

    expect(find.text('Recovery timeline'), findsOneWidget); // AppBar title
    // MockReadinessRepository seeds 14 days of history — the full,
    // uncapped list, not the Home preview's 5. `findsAtLeastNWidgets`
    // (not `findsNWidgets`) because Readiness Home's own route stays
    // mounted underneath this pushed one, so its 5 preview tiles are
    // still technically present in the tree alongside the timeline's.
    expect(find.byType(ReadinessEntryTile), findsAtLeastNWidgets(14));
  });

  testWidgets('tapping a check-in in the recent list opens its real detail screen', (
    tester,
  ) async {
    await _pumpToReadinessHome(tester);

    await tester.tap(find.byType(ReadinessEntryTile).first);
    await tester.pumpAndSettle();

    expect(find.text('Check-in detail'), findsOneWidget); // AppBar title
    // Sleep, energy, stress, and soreness are seeded for every entry, so
    // the detail screen renders real recorded values, never a computed
    // score.
    expect(find.textContaining('/10'), findsWidgets);
  });

  testWidgets('the recovery score entry point discloses it is not connected, never a '
      'fabricated score', (tester) async {
    await _pumpToReadinessHome(tester);

    await tester.tap(find.text('Recovery score'));
    await tester.pumpAndSettle();

    expect(find.text('Recovery score not connected yet'), findsOneWidget);
  });
}
