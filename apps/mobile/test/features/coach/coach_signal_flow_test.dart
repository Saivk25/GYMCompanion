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
import 'package:gym_companion_mobile/features/today/application/today_controller.dart';
import 'package:gym_companion_mobile/features/today/infrastructure/mock_today_repository.dart';
import 'package:gym_companion_mobile/features/train/application/train_controller.dart';
import 'package:gym_companion_mobile/features/train/infrastructure/mock_train_repository.dart';
import 'package:gym_companion_mobile/shared/application/coach_signal_log.dart';
import '../../support/auth_test_overrides.dart';

/// End-to-end through the real router, the real `CoachSignalLog`, and
/// every real mock repository — proving the actual cross-module wiring
/// this module's own architecture depends on: a real action in Today/
/// Readiness genuinely produces a signal Coach genuinely displays,
/// with no fabrication anywhere in the path. Mirrors the reasoning
/// `checkin_flow_test.dart`/`log_meal_flow_test.dart` give for testing
/// this way rather than a narrower unit test.
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

void main() {
  testWidgets(
    'submitting a real readiness check-in makes its real warnings appear on Coach Home',
    (tester) async {
      await tester.pumpWidget(_appWithMocks());
      await tester.pumpAndSettle();

      // Today's check-in nudge -> the real check-in screen -> submit with
      // every field at its pre-filled default. `MockReadinessRepository
      // .submitCheckIn` returns two real illustrative warnings on this,
      // the very first submission.
      await tester.tap(find.text('Complete check-in'));
      await tester.pumpAndSettle();
      // The check-in form has several fields above the submit button, so
      // it can sit below the fold — see checkin_flow_test.dart's
      // identical fix: unconditional drag first, then ensureVisible.
      final Finder submitButton = find.widgetWithText(ElevatedButton, 'Submit check-in');
      await tester.drag(find.byType(Scrollable).first, const Offset(0, -400));
      await tester.pumpAndSettle();
      await tester.ensureVisible(submitButton);
      await tester.pumpAndSettle();
      await tester.tap(submitButton);
      await tester.pumpAndSettle();

      // Back on Today. Coach Home has no route of its own reachable from
      // here except the bottom tab — switch to it directly.
      await tester.tap(find.text('Coach').last);
      await tester.pumpAndSettle();

      // The exact illustrative text `MockReadinessRepository` returns.
      expect(
        find.textContaining('Example advisory — real recommendations come from the backend'),
        findsWidgets,
      );
      expect(find.text('Nothing to show yet'), findsNothing);
    },
  );

  testWidgets(
    'a session with no actions taken yet shows Coach Home genuinely empty, never fabricated',
    (tester) async {
      await tester.pumpWidget(_appWithMocks());
      await tester.pumpAndSettle();

      await tester.tap(find.text('Coach').last);
      await tester.pumpAndSettle();

      expect(find.text('Nothing to show yet'), findsOneWidget);
    },
  );
}
