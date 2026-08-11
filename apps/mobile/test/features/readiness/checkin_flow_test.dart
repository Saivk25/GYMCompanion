import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/app.dart';
import 'package:gym_companion_mobile/features/coach/application/coach_controller.dart';
import 'package:gym_companion_mobile/features/coach/infrastructure/mock_coach_repository.dart';
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
import 'package:gym_companion_mobile/shared/application/coach_signal_log.dart';
import '../../support/auth_test_overrides.dart';

/// End-to-end through the real router and [MockReadinessRepository] —
/// the same reasoning `log_meal_flow_test.dart`/`log_measurement_flow_
/// test.dart` give for doing this rather than a narrower unit test.
ProviderScope _appWithMocks() {
  return ProviderScope(
    overrides: <Override>[
        ...authenticatedTestOverrides(),
      todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
      trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
      fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
      progressRepositoryProvider.overrideWithValue(MockProgressRepository()),
      readinessRepositoryProvider.overrideWithValue(MockReadinessRepository()),
      coachRepositoryProvider.overrideWith(
        (ref) => MockCoachRepository(() => ref.read(coachSignalLogProvider)),
      ),
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
  // The Recovery segment's content is taller than the 600px test
  // viewport — "Readiness check-ins" sits below the fold. Neither
  // ensureVisible nor scrollUntilVisible alone is reliable here:
  // ensureVisible needs the element already built (throws if it's far
  // enough below the fold that Sliver virtualization hasn't built it),
  // and scrollUntilVisible's loop only scrolls while the finder is
  // empty — since this target IS already built (just off-screen), that
  // loop never runs and silently does nothing. An unconditional drag
  // first, then ensureVisible for exact positioning, handles both.
  final Finder readinessLink = find.text('Readiness check-ins');
  await tester.drag(find.byType(Scrollable).first, const Offset(0, -400));
  await tester.pumpAndSettle();
  await tester.ensureVisible(readinessLink);
  await tester.pumpAndSettle();
  await tester.tap(readinessLink);
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

    // See _pumpToReadinessHome's comment: this link can sit below the
    // fold and needs an unconditional drag before ensureVisible.
    final Finder startCheckIn = find.text('Start check-in');
    await tester.drag(find.byType(Scrollable).first, const Offset(0, -400));
    await tester.pumpAndSettle();
    await tester.ensureVisible(startCheckIn);
    await tester.pumpAndSettle();
    await tester.tap(startCheckIn);
    await tester.pumpAndSettle();

    expect(find.text('Readiness check-in'), findsOneWidget);
    final Finder submitButton = find.widgetWithText(ElevatedButton, 'Submit check-in');
    // The form has several fields above it, so the submit button itself
    // can sit below the fold — same reasoning as above.
    await tester.drag(find.byType(Scrollable).first, const Offset(0, -400));
    await tester.pumpAndSettle();
    await tester.ensureVisible(submitButton);
    await tester.pumpAndSettle();
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
    // TD-0010 (`docs/TECH_DEBT.md`): the timeline is now a genuinely
    // lazy `ListView.builder` — only rows near the viewport are built,
    // not all 14 seeded entries at once. Readiness Home's own route
    // stays mounted underneath this pushed one, so the total found here
    // is "5 preview tiles + however many timeline rows currently fit on
    // screen" — well under "5 + all 14", which is exactly the laziness
    // this conversion was for.
    expect(find.byType(ReadinessEntryTile), findsWidgets);
    expect(tester.widgetList(find.byType(ReadinessEntryTile)).length, lessThan(5 + 14));

    // MockReadinessRepository seeds 14 days of history, oldest last
    // (the repository's own newest-first order) — scrolling the
    // timeline's own list (scoped via the `ClipRRect` this screen wraps
    // it in, so this can't accidentally match Home's list underneath)
    // to its end must still reach that oldest, 14th entry, proving the
    // full, uncapped list is reachable even though it isn't all built
    // at once. Its sleep/energy combination (8.0h, energy 6) is unique
    // across all 14 seeded entries (`mock_readiness_repository.dart`),
    // so matching this text is a real check of *which* entry scrolled
    // into view, not just that *some* row did.
    final Finder timelineList = find.descendant(
      of: find.byType(ClipRRect),
      matching: find.byType(ListView),
    );
    await tester.fling(timelineList, const Offset(0, -3000), 3000);
    await tester.pumpAndSettle();

    expect(find.text('8.0h sleep · energy 6/10 · stress 4/10'), findsOneWidget);
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

    // MockReadinessRepository's full 14-day seed pushes this well below
    // the fold — unconditional drag first, then ensureVisible.
    final Finder recoveryScore = find.text('Recovery score');
    await tester.drag(find.byType(Scrollable).first, const Offset(0, -400));
    await tester.pumpAndSettle();
    await tester.ensureVisible(recoveryScore);
    await tester.pumpAndSettle();
    await tester.tap(recoveryScore);
    await tester.pumpAndSettle();

    expect(find.text('Recovery score not connected yet'), findsOneWidget);
  });

  testWidgets(
      'TD-0013: check-in text fields chain keyboard focus, ending with a '
      "done action that doesn't submit the form", (tester) async {
    await _pumpToReadinessHome(tester);

    final Finder startCheckIn = find.text('Start check-in');
    await tester.drag(find.byType(Scrollable).first, const Offset(0, -400));
    await tester.pumpAndSettle();
    await tester.ensureVisible(startCheckIn);
    await tester.pumpAndSettle();
    await tester.tap(startCheckIn);
    await tester.pumpAndSettle();

    // Declared order in ReadinessCheckInScreen.build(): Hours, Resting HR,
    // HRV, then Notes last — the four AppRatingSlider fields in between
    // (Sleep quality, Energy, Stress, Soreness) aren't text-focusable, so
    // they don't appear as TextFields at all. Every text field but Notes
    // chains to the next via the keyboard's "Next" action; Notes uses
    // "Done" and just dismisses (see readiness_checkin_screen.dart's
    // onSubmitted) — the real submit button is always enabled here, so
    // there's no gating state Notes' submission would need to trigger.
    final Finder fields = find.byType(TextField);
    expect(fields, findsNWidgets(4));
    for (int i = 0; i < 3; i++) {
      expect(tester.widget<TextField>(fields.at(i)).textInputAction, TextInputAction.next);
    }
    expect(tester.widget<TextField>(fields.at(3)).textInputAction, TextInputAction.done);
  });
}
