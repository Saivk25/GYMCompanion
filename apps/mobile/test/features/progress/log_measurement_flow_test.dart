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
import 'package:gym_companion_mobile/features/today/application/today_controller.dart';
import 'package:gym_companion_mobile/features/today/infrastructure/mock_today_repository.dart';
import 'package:gym_companion_mobile/features/train/application/train_controller.dart';
import 'package:gym_companion_mobile/features/train/infrastructure/mock_train_repository.dart';
import 'package:gym_companion_mobile/shared/application/coach_signal_log.dart';
import '../../support/auth_test_overrides.dart';

/// End-to-end through the real router and [MockProgressRepository] —
/// the same reasoning `log_meal_flow_test.dart` gives for doing this
/// rather than a narrower unit test.
Future<void> _pumpToProgressTransformation(WidgetTester tester) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: <Override>[
        ...authenticatedTestOverrides(),
        todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
        trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
        fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
        progressRepositoryProvider.overrideWithValue(MockProgressRepository()),
        coachRepositoryProvider.overrideWith(
          (ref) => MockCoachRepository(() => ref.read(coachSignalLogProvider)),
        ),
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

    // See readiness_home_screen_test.dart's identical fix: this link can
    // sit below the fold. An unconditional drag first, then ensureVisible
    // for exact positioning — scrollUntilVisible alone doesn't work when
    // the target is already built (just off-screen), since its loop only
    // scrolls while the finder comes up empty.
    final Finder logMeasurements = find.text('Log measurements');
    await tester.drag(find.byType(Scrollable).first, const Offset(0, -400));
    await tester.pumpAndSettle();
    await tester.ensureVisible(logMeasurements);
    await tester.pumpAndSettle();
    await tester.tap(logMeasurements);
    await tester.pumpAndSettle();

    expect(find.text('Log measurements'), findsOneWidget); // the AppBar title
    final Finder submitButton = find.widgetWithText(ElevatedButton, 'Log check-in');
    // The form has several fields above the submit button, so it can
    // also sit below the fold — same reasoning as above.
    //
    // ensureVisible's default alignment (0.0, edge-align — this SDK's
    // WidgetController.ensureVisible has no `alignment` parameter to
    // override it) left the button's tap center computed at just past
    // the 600px viewport edge (a real trace showed Offset(400, 606),
    // outside Size(800, 600)), causing a silent hit-test-miss no-op tap.
    // A small extra drag after ensureVisible nudges the button away from
    // that exact boundary and into real margin — there's more form
    // content above it to scroll through, so this can't overshoot past
    // the top.
    await tester.drag(find.byType(Scrollable).first, const Offset(0, -400));
    await tester.pumpAndSettle();
    await tester.ensureVisible(submitButton);
    await tester.pumpAndSettle();
    await tester.drag(find.byType(Scrollable).first, const Offset(0, -60));
    await tester.pumpAndSettle();
    expect(tester.widget<ElevatedButton>(submitButton).onPressed, isNull);

    await tester.enterText(find.widgetWithText(TextField, 'Weight (kg)'), '77.5');
    await tester.pump();
    expect(tester.widget<ElevatedButton>(submitButton).onPressed, isNotNull);

    // Entering text can shift this button's position (e.g. a validation
    // hint appearing/disappearing above it), so re-resolve its on-screen
    // position immediately before tapping rather than reusing the
    // position from before text entry.
    await tester.ensureVisible(submitButton);
    await tester.pumpAndSettle();
    await tester.drag(find.byType(Scrollable).first, const Offset(0, -60));
    await tester.pumpAndSettle();
    await tester.tap(submitButton);
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

    // See readiness_home_screen_test.dart's identical fix: unconditional
    // drag first, then ensureVisible.
    final Finder newPhotoCheckIn = find.text('New photo check-in');
    await tester.drag(find.byType(Scrollable).first, const Offset(0, -400));
    await tester.pumpAndSettle();
    await tester.ensureVisible(newPhotoCheckIn);
    await tester.pumpAndSettle();
    await tester.tap(newPhotoCheckIn);
    await tester.pumpAndSettle();

    expect(find.text('Photo check-in not connected yet'), findsOneWidget);
  });

  testWidgets('photo comparison is reachable from Transformation and discloses it '
      "isn't connected", (tester) async {
    await _pumpToProgressTransformation(tester);

    // See readiness_home_screen_test.dart's identical fix: unconditional
    // drag first, then ensureVisible.
    final Finder comparePhotos = find.text('Compare photos');
    await tester.drag(find.byType(Scrollable).first, const Offset(0, -400));
    await tester.pumpAndSettle();
    await tester.ensureVisible(comparePhotos);
    await tester.pumpAndSettle();
    await tester.tap(comparePhotos);
    await tester.pumpAndSettle();

    expect(find.text('Photo comparison not connected yet'), findsOneWidget);
  });

  testWidgets('correlations is reachable from Recovery and discloses it '
      "isn't connected", (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
        ...authenticatedTestOverrides(),
          todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
          trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
          fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
          progressRepositoryProvider.overrideWithValue(MockProgressRepository()),
          coachRepositoryProvider.overrideWith(
            (ref) => MockCoachRepository(() => ref.read(coachSignalLogProvider)),
          ),
        ],
        child: const GymCompanionApp(),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Progress').last);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Recovery'));
    await tester.pumpAndSettle();

    // See readiness_home_screen_test.dart's identical fix: unconditional
    // drag first, then ensureVisible.
    final Finder correlations = find.text('Correlations');
    await tester.drag(find.byType(Scrollable).first, const Offset(0, -400));
    await tester.pumpAndSettle();
    await tester.ensureVisible(correlations);
    await tester.pumpAndSettle();
    await tester.tap(correlations);
    await tester.pumpAndSettle();

    expect(find.text('Correlations not connected yet'), findsOneWidget);
  });

  testWidgets(
      'TD-0013: measurement fields chain keyboard focus, ending with a '
      "done action that doesn't submit the form", (tester) async {
    await _pumpToProgressTransformation(tester);

    await tester.drag(find.byType(Scrollable).first, const Offset(0, -400));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('Log measurements'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Log measurements'));
    await tester.pumpAndSettle();

    // Declared order in LogMeasurementScreen.build(): Weight, Body fat,
    // Lean mass, Muscle mass, Waist, Chest, Hip, Arm, Thigh, Calf, Neck,
    // then Notes last. Every field but Notes chains to the next via the
    // keyboard's "Next" action; Notes uses "Done" and just dismisses,
    // since the real submit button stays separately gated on _canSubmit.
    final Finder fields = find.byType(TextField);
    expect(fields, findsNWidgets(12));
    for (int i = 0; i < 11; i++) {
      expect(tester.widget<TextField>(fields.at(i)).textInputAction, TextInputAction.next);
    }
    expect(tester.widget<TextField>(fields.at(11)).textInputAction, TextInputAction.done);
  });
}
