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
import '../../support/auth_test_overrides.dart';

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
        ...authenticatedTestOverrides(),
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

  // "Start session" can sit below the fold on shorter viewports.
  // ensureVisible alone (no preceding coarse drag) — PreSessionScreen's
  // content is short and TierPicker has no nested Scrollable, so the
  // button is already built; a coarse drag here isn't needed and risks
  // disturbing the tap's timing relative to this screen's animations.
  final Finder startSession = find.text('Start session');
  await tester.ensureVisible(startSession);
  await tester.pumpAndSettle();
  await tester.tap(startSession);
  await tester.pump();
  // Two delays happen back-to-back here, not one: `_startSession` awaits
  // `MockTrainRepository.startSession`'s own 300ms delay, then calls
  // `context.pushReplacement` into Active Workout — whose
  // `ActiveSessionController.build` immediately calls
  // `fetchSession(sessionId)`, a *second* 300ms `_delay()` on the same
  // repository (`train_controller.dart`'s `ActiveSessionController.
  // build`). A single 350ms pump only covers the first delay, so the
  // route always arrived with its own fetch still pending — this, not
  // scrolling or tap targeting, was the actual reason "Exercise 1 of 3"
  // never appeared. Two pumps, one per delay.
  await tester.pump(const Duration(milliseconds: 350));
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
    // A single 350ms pump (enough for completeSession's own 300ms delay)
    // wasn't enough here even though SessionSummaryScreen reads the same
    // keep-alive `activeSessionControllerProvider` family instance
    // Active Workout already populated (AsyncNotifierProvider.family,
    // not autoDispose, so no second fetchSession fetch is expected) —
    // this route is reached via a *second* consecutive
    // `pushReplacement` (Pre-session -> Active Workout was already one),
    // and GoRouter evidently needs more than one settle cycle to land
    // on it. Same generous two-pump budget as `_pumpToActiveWorkout`'s
    // own start-session transition, for the same reason: better to give
    // real margin than chase the exact frame count.
    await tester.pump(const Duration(milliseconds: 350));
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
