import 'package:flutter/material.dart';
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

/// End-to-end through the real router and [MockTrainRepository] — not a
/// narrower unit test — because the value worth verifying here is the
/// whole logging *flow* (Pre-session's tier choice through Active
/// Workout's set-log/complete/rest-timer/end-session sequence), which no
/// single screen's isolated test would exercise. [MockTrainRepository]'s
/// own in-memory session store (see that file's doc comment) is what
/// makes this possible without a real backend.
///
/// ## Why bounded `pump()` calls, not `pumpAndSettle()`, past this point
///
/// `ActiveWorkoutScreen` runs a real `Timer.periodic` for its elapsed-
/// time display the whole time it is mounted (`active_workout_screen.
/// dart`'s own doc comment) — a live, indefinitely-repeating timer that
/// keeps scheduling frames. `pumpAndSettle()` waits for frame scheduling
/// to stop entirely, which a screen with a genuinely never-stopping
/// ticker cannot satisfy; using it here risks a flaky "pumpAndSettle
/// timed out" failure rather than a real assertion failure. Every step
/// below Active Workout uses `pump()` with an explicit duration covering
/// the specific mock delay involved (`MockTrainRepository`'s own 80ms
/// logging delay, 300ms for session start/complete) instead.
Future<void> _pumpToActiveWorkout(WidgetTester tester) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: <Override>[
        todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
        trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
        coachRepositoryProvider.overrideWith(
          (ref) => MockCoachRepository(() => ref.read(coachSignalLogProvider)),
        ),
      ],
      child: const GymCompanionApp(),
    ),
  );
  await tester.pumpAndSettle();

  await tester.tap(find.text('Train').last);
  await tester.pumpAndSettle();

  await tester.tap(find.text('Upper Body Strength').first);
  await tester.pumpAndSettle();

  await tester.tap(find.text('Start session'));
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 350));
}

void main() {
  testWidgets('starting a session opens Active Workout on the first exercise', (
    tester,
  ) async {
    await _pumpToActiveWorkout(tester);

    expect(find.text('Exercise 1 of 3'), findsOneWidget);
    expect(find.text('Set 1'), findsOneWidget);
  });

  testWidgets('logging a set shows it awaiting confirmation, then completing it '
      'starts the rest timer', (tester) async {
    await _pumpToActiveWorkout(tester);

    final Finder fields = find.byType(TextField);
    expect(fields, findsNWidgets(3));
    await tester.enterText(fields.at(0), '60');
    await tester.enterText(fields.at(1), '8');
    await tester.enterText(fields.at(2), '7');
    await tester.pump();

    await tester.tap(find.text('Log set'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 150));

    expect(find.textContaining('60 × 8 @ RPE 7'), findsOneWidget);
    expect(find.text('Mark complete'), findsOneWidget);
    expect(find.textContaining('Resting'), findsNothing);

    await tester.tap(find.text('Mark complete'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 150));

    expect(find.textContaining('Resting'), findsOneWidget);
    expect(find.text('Skip'), findsOneWidget);

    await tester.tap(find.text('Skip'));
    await tester.pump();
    expect(find.textContaining('Resting'), findsNothing);
  });

  testWidgets('ending the session navigates to the summary screen with "Return '
      'to Today"', (tester) async {
    await _pumpToActiveWorkout(tester);

    await tester.tap(find.text('End session'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 350));

    expect(find.text('Session summary'), findsOneWidget);
    expect(find.text('Return to Today'), findsOneWidget);
  });

  testWidgets('viewing cues for an exercise opens the honest not-connected '
      'placeholder', (tester) async {
    await _pumpToActiveWorkout(tester);

    await tester.tap(find.text('Cues'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));

    expect(find.text('Cues and history not connected yet'), findsOneWidget);
  });
}
