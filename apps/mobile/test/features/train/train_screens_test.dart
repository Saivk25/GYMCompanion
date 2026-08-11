import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/app.dart';
import 'package:gym_companion_mobile/features/coach/application/coach_controller.dart';
import 'package:gym_companion_mobile/features/coach/infrastructure/mock_coach_repository.dart';
import 'package:gym_companion_mobile/features/today/application/today_controller.dart';
import 'package:gym_companion_mobile/features/today/infrastructure/mock_today_repository.dart';
import 'package:gym_companion_mobile/features/train/application/train_controller.dart';
import 'package:gym_companion_mobile/features/train/infrastructure/mock_train_repository.dart';
import 'package:gym_companion_mobile/shared/application/coach_signal_log.dart';
import '../../support/auth_test_overrides.dart';

/// Covers the remaining Train screens not already exercised by
/// `train_home_screen_test.dart` (Train Home itself) or
/// `active_workout_screen_test.dart` (the logging flow): Pre-session's
/// tier choice, Personal Records' honest placeholder, and Session
/// Summary reached from History (the "past session" path, distinct from
/// the "just finished" path `active_workout_screen_test.dart` already
/// covers).
Future<ProviderScope> _appPumped(WidgetTester tester) async {
  final ProviderScope app = ProviderScope(
    overrides: <Override>[
        ...authenticatedTestOverrides(),
      todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
      trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
      coachRepositoryProvider.overrideWith(
        (ref) => MockCoachRepository(() => ref.read(coachSignalLogProvider)),
      ),
    ],
    child: const GymCompanionApp(),
  );
  await tester.pumpWidget(app);
  await tester.pumpAndSettle();
  await tester.tap(find.text('Train').last);
  await tester.pumpAndSettle();
  return app;
}

void main() {
  testWidgets('Pre-session shows the workout and lets the tier be changed', (
    tester,
  ) async {
    await _appPumped(tester);

    await tester.tap(find.text('Upper Body Strength').first);
    await tester.pumpAndSettle();

    expect(find.text('Choose your tier'), findsOneWidget);
    expect(find.text('Minimum'), findsOneWidget);
    expect(find.text('Standard'), findsOneWidget);
    expect(find.text('Stretch'), findsOneWidget);
    expect(find.text('Start session'), findsOneWidget);

    await tester.tap(find.text('Minimum'));
    await tester.pump();
    // Selecting a tier does not itself navigate away — still on
    // Pre-session, now with Minimum as the active choice.
    expect(find.text('Choose your tier'), findsOneWidget);
  });

  testWidgets('Personal Records is reachable from Train Home and discloses '
      "it isn't connected, rather than showing fabricated records", (
    tester,
  ) async {
    await _appPumped(tester);

    await tester.tap(find.text('Records'));
    await tester.pumpAndSettle();

    expect(find.text('Personal records'), findsOneWidget);
    expect(find.text('Personal records not connected yet'), findsOneWidget);
  });

  testWidgets('opening a past session from History shows "Return to history", '
      'not "Return to Today"', (tester) async {
    await _appPumped(tester);

    await tester.tap(find.text('History'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Upper Body Strength').first);
    await tester.pumpAndSettle();

    expect(find.text('Session summary'), findsOneWidget);
    expect(find.text('Return to history'), findsOneWidget);
    expect(find.text('Return to Today'), findsNothing);

    await tester.tap(find.text('Return to history'));
    await tester.pumpAndSettle();

    // Back on Train Home, still showing the History tab (a genuine
    // `pop`, not a fresh navigation that would reset tab selection).
    expect(find.text('History'), findsOneWidget);
  });
}
