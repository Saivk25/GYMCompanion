import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/app.dart';
import 'package:gym_companion_mobile/core/cache/cache.dart';
import 'package:gym_companion_mobile/design/design.dart';
import 'package:gym_companion_mobile/features/auth/application/auth_controller.dart';
import 'package:gym_companion_mobile/features/auth/infrastructure/mock_auth_repository.dart';
import 'package:gym_companion_mobile/features/coach/application/coach_controller.dart';
import 'package:gym_companion_mobile/features/coach/infrastructure/mock_coach_repository.dart';
import 'package:gym_companion_mobile/features/coach/presentation/coach_home_screen.dart';
import 'package:gym_companion_mobile/features/fuel/application/fuel_controller.dart';
import 'package:gym_companion_mobile/features/fuel/infrastructure/mock_fuel_repository.dart';
import 'package:gym_companion_mobile/features/progress/application/progress_controller.dart';
import 'package:gym_companion_mobile/features/progress/infrastructure/mock_progress_repository.dart';
import 'package:gym_companion_mobile/features/readiness/application/readiness_controller.dart';
import 'package:gym_companion_mobile/features/readiness/infrastructure/mock_readiness_repository.dart';
import 'package:gym_companion_mobile/features/readiness/presentation/widgets/readiness_entry_tile.dart';
import 'package:gym_companion_mobile/features/today/application/today_controller.dart';
import 'package:gym_companion_mobile/features/today/infrastructure/mock_today_repository.dart';
import 'package:gym_companion_mobile/features/today/presentation/today_screen.dart';
import 'package:gym_companion_mobile/features/train/application/train_controller.dart';
import 'package:gym_companion_mobile/features/train/infrastructure/mock_train_repository.dart';
import 'package:gym_companion_mobile/shared/application/coach_signal_log.dart';
import 'package:gym_companion_mobile/shared/domain/coach_signal.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../support/auth_test_overrides.dart';

/// TD-0014 (`docs/TECH_DEBT.md`): the automatable subset of `docs/adr/
/// 0042-production-integration-plan.md` Part 5/Part 6's own accessibility
/// findings — `flutter_test`'s built-in `meetsGuideline` matchers, which
/// need only the widget-test harness (no real device/TalkBack/VoiceOver;
/// see `docs/adr/0002`'s own standing constraint).
///
/// Originally run against two representative screens (Today, Coach Home)
/// to prove the check was wired correctly. Now widened to every reachable
/// screen in the app except `SplashScreen` — a bare `CircularProgressIndicator`
/// with no text and no tappable element, so `meetsGuideline` would pass on
/// it vacuously (no semantics nodes to violate either guideline); a "test"
/// with no possible failure mode is not real coverage, so it's excluded
/// rather than padding the count. Every other screen reached by the app's
/// real router — auth, all five tabs, and every drill-in — gets its own
/// pump-and-check pair, reusing the exact navigation sequences this
/// suite's own `*_flow_test.dart`/`*_screen_test.dart` files already prove
/// work (scroll-then-`ensureVisible` for below-the-fold targets, bounded
/// `pump()` instead of `pumpAndSettle()` past Active Workout's live
/// `Timer.periodic`, etc.) — see each test's own comment for which sibling
/// file its sequence is copied from.
List<Override> _fullMockOverrides() => <Override>[
      ...authenticatedTestOverrides(),
      todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
      trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
      fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
      progressRepositoryProvider.overrideWithValue(MockProgressRepository()),
      readinessRepositoryProvider.overrideWithValue(MockReadinessRepository()),
      coachRepositoryProvider.overrideWith(
        (ref) => MockCoachRepository(() => ref.read(coachSignalLogProvider)),
      ),
    ];

Future<void> _pumpApp(WidgetTester tester) async {
  await tester.pumpWidget(
    ProviderScope(overrides: _fullMockOverrides(), child: const GymCompanionApp()),
  );
  await tester.pumpAndSettle();
}

Future<void> _checkGuideline(WidgetTester tester) async {
  await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
  await expectLater(tester, meetsGuideline(textContrastGuideline));
}

/// Shared by every "scroll to a below-the-fold target" step — the same
/// unconditional-drag-then-`ensureVisible` pattern this suite's own
/// `readiness_home_screen_test.dart`/`coach_home_screen_test.dart`/
/// `log_measurement_flow_test.dart` all independently established (see
/// `_pumpToReadinessHome`'s own comment there for why neither tool works
/// alone).
Future<void> _scrollToAndTap(WidgetTester tester, Finder finder) async {
  await tester.drag(find.byType(Scrollable).first, const Offset(0, -400));
  await tester.pumpAndSettle();
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('Today meets Android tap-target and text-contrast guidelines', (
    WidgetTester tester,
  ) async {
    final SemanticsHandle handle = tester.ensureSemantics();
    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
          todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
        ],
        child: MaterialApp(theme: AppTheme.light, home: const Scaffold(body: TodayScreen())),
      ),
    );
    await tester.pumpAndSettle();

    await _checkGuideline(tester);

    handle.dispose();
  });

  testWidgets('Coach Home (with real signals and filters rendered) meets '
      'Android tap-target and text-contrast guidelines', (WidgetTester tester) async {
    final SemanticsHandle handle = tester.ensureSemantics();
    final CoachSignal signal = CoachSignal(
      id: 's1',
      module: CoachModule.recovery,
      severity: CoachSeverity.warning,
      message: 'Sleep has been below target.',
      occurredAt: DateTime.now(),
    );
    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
          coachRepositoryProvider.overrideWithValue(_FixedCoachRepository(<CoachSignal>[signal])),
        ],
        child: MaterialApp(theme: AppTheme.light, home: const Scaffold(body: CoachHomeScreen())),
      ),
    );
    await tester.pumpAndSettle();

    await _checkGuideline(tester);

    handle.dispose();
  });

  group('Auth', () {
    // Mirrors auth_flow_test.dart's own `_pumpUnauthenticatedApp`: needs
    // an unauthenticated token store and a real (mocked) SharedPreferences
    // instance behind localCacheProvider, the same pair that file's own
    // comment explains every unauthenticated-start test needs.
    Future<void> pumpUnauthenticatedApp(WidgetTester tester) async {
      SharedPreferences.setMockInitialValues(<String, Object>{});
      final SharedPreferences prefs = await SharedPreferences.getInstance();
      await tester.pumpWidget(
        ProviderScope(
          overrides: <Override>[
            todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
            trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
            fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
            progressRepositoryProvider.overrideWithValue(MockProgressRepository()),
            readinessRepositoryProvider.overrideWithValue(MockReadinessRepository()),
            coachRepositoryProvider.overrideWith(
              (ref) => MockCoachRepository(() => ref.read(coachSignalLogProvider)),
            ),
            authRepositoryProvider.overrideWithValue(const MockAuthRepository()),
            tokenStorageProvider.overrideWithValue(MockTokenStorage(seedRefreshToken: null)),
            localCacheProvider.overrideWithValue(LocalCache(prefs)),
          ],
          child: const GymCompanionApp(),
        ),
      );
      await tester.pumpAndSettle();
    }

    testWidgets('Login meets Android tap-target and text-contrast guidelines', (tester) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await pumpUnauthenticatedApp(tester);

      expect(find.text('Sign in to continue'), findsOneWidget);
      await _checkGuideline(tester);

      handle.dispose();
    });

    testWidgets('Register meets Android tap-target and text-contrast guidelines', (tester) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await pumpUnauthenticatedApp(tester);
      await tester.tap(find.text("Don't have an account? Create one"));
      await tester.pumpAndSettle();

      expect(find.widgetWithText(AppBar, 'Create account'), findsOneWidget);
      await _checkGuideline(tester);

      handle.dispose();
    });
  });

  group('Train', () {
    // See active_workout_screen_test.dart's own comment: ActiveWorkoutScreen
    // runs a live Timer.periodic the whole time it's mounted, so this
    // sequence uses bounded pump() rather than pumpAndSettle() past this
    // point, copied verbatim from that file's own `_pumpToActiveWorkout`.
    Future<void> pumpToActiveWorkout(WidgetTester tester) async {
      await _pumpApp(tester);
      await tester.tap(find.text('Train').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Upper Body Strength').first);
      await tester.pumpAndSettle();
      final Finder startSession = find.text('Start session');
      await tester.ensureVisible(startSession);
      await tester.pumpAndSettle();
      await tester.tap(startSession);
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 350));
      await tester.pump(const Duration(milliseconds: 350));
    }

    testWidgets('Train Home meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await _pumpApp(tester);
      await tester.tap(find.text('Train').last);
      await tester.pumpAndSettle();

      await _checkGuideline(tester);

      handle.dispose();
    });

    testWidgets('Pre-session meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await _pumpApp(tester);
      await tester.tap(find.text('Train').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Upper Body Strength').first);
      await tester.pumpAndSettle();

      expect(find.text('Choose your tier'), findsOneWidget);
      await _checkGuideline(tester);

      handle.dispose();
    });

    testWidgets('Active Workout meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await pumpToActiveWorkout(tester);

      expect(find.text('Exercise 1 of 3'), findsOneWidget);
      await _checkGuideline(tester);

      handle.dispose();
    });

    testWidgets('Exercise Detail (Cues) meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await pumpToActiveWorkout(tester);
      await tester.tap(find.text('Cues'));
      await tester.pump();
      // active_workout_screen_test.dart's own "viewing cues" test only
      // pumps 50ms here, but that test only asserts the placeholder text
      // exists in the tree — tolerant of a still-mid-transition page.
      // meetsGuideline instead inspects actual rendered color/opacity, so
      // it needs the push route's page-transition animation (Flutter's
      // default ~300ms) to actually finish; 50ms caught it still fading
      // in, compositing near-white text over the previous route's white
      // background and reading as a false contrast failure. Still a
      // bounded pump, not pumpAndSettle() — Active Workout stays mounted
      // underneath this pushed route with its own live Timer.periodic
      // still ticking (see pumpToActiveWorkout's own comment), so
      // pumpAndSettle() here would hang the same way it would on that
      // screen directly.
      await tester.pump(const Duration(milliseconds: 300));

      expect(find.text('Cues and history not connected yet'), findsOneWidget);
      await _checkGuideline(tester);

      handle.dispose();
    });

    testWidgets('Session Summary meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await _pumpApp(tester);
      await tester.tap(find.text('Train').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('History'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Upper Body Strength').first);
      await tester.pumpAndSettle();

      expect(find.text('Session summary'), findsOneWidget);
      await _checkGuideline(tester);

      handle.dispose();
    });

    testWidgets('Personal Records meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await _pumpApp(tester);
      await tester.tap(find.text('Train').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Records'));
      await tester.pumpAndSettle();

      expect(find.text('Personal records not connected yet'), findsOneWidget);
      await _checkGuideline(tester);

      handle.dispose();
    });
  });

  group('Fuel', () {
    testWidgets('Fuel Home meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await _pumpApp(tester);
      await tester.tap(find.text('Fuel').last);
      await tester.pumpAndSettle();

      await _checkGuideline(tester);

      handle.dispose();
    });

    testWidgets('Log a meal meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await _pumpApp(tester);
      await tester.tap(find.text('Fuel').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Log a meal'));
      await tester.pumpAndSettle();

      expect(find.text('Log meal'), findsOneWidget);
      await _checkGuideline(tester);

      handle.dispose();
    });

    testWidgets('Food Search meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await _pumpApp(tester);
      await tester.tap(find.text('Fuel').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Log a meal'));
      await tester.pumpAndSettle();
      await tester.tap(find.byTooltip('Search foods'));
      await tester.pumpAndSettle();

      expect(find.text('Food search not connected yet'), findsOneWidget);
      await _checkGuideline(tester);

      handle.dispose();
    });

    testWidgets('Supplements meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await _pumpApp(tester);
      await tester.tap(find.text('Fuel').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Supplements'));
      await tester.pumpAndSettle();

      expect(find.text('Supplement tracking not connected yet'), findsOneWidget);
      await _checkGuideline(tester);

      handle.dispose();
    });
  });

  group('Progress', () {
    testWidgets('Progress Home meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await _pumpApp(tester);
      await tester.tap(find.text('Progress').last);
      await tester.pumpAndSettle();

      await _checkGuideline(tester);

      handle.dispose();
    });

    testWidgets('Log measurements meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await _pumpApp(tester);
      await tester.tap(find.text('Progress').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Transformation'));
      await tester.pumpAndSettle();
      await _scrollToAndTap(tester, find.text('Log measurements'));

      expect(find.text('Log measurements'), findsOneWidget);
      await _checkGuideline(tester);

      handle.dispose();
    });

    testWidgets('Measurement Trend meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await _pumpApp(tester);
      await tester.tap(find.text('Progress').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Transformation'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Weight, rolling average'));
      await tester.pumpAndSettle();

      expect(find.text('Weight'), findsWidgets); // AppBar title + list row label
      await _checkGuideline(tester);

      handle.dispose();
    });

    testWidgets('Photo Check-in meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await _pumpApp(tester);
      await tester.tap(find.text('Progress').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Transformation'));
      await tester.pumpAndSettle();
      await _scrollToAndTap(tester, find.text('New photo check-in'));

      expect(find.text('Photo check-in not connected yet'), findsOneWidget);
      await _checkGuideline(tester);

      handle.dispose();
    });

    testWidgets('Photo Comparison meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await _pumpApp(tester);
      await tester.tap(find.text('Progress').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Transformation'));
      await tester.pumpAndSettle();
      await _scrollToAndTap(tester, find.text('Compare photos'));

      expect(find.text('Photo comparison not connected yet'), findsOneWidget);
      await _checkGuideline(tester);

      handle.dispose();
    });

    testWidgets('Insights (Correlations) meets Android tap-target and text-contrast '
        'guidelines', (tester) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await _pumpApp(tester);
      await tester.tap(find.text('Progress').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Recovery'));
      await tester.pumpAndSettle();
      await _scrollToAndTap(tester, find.text('Correlations'));

      expect(find.text('Correlations not connected yet'), findsOneWidget);
      await _checkGuideline(tester);

      handle.dispose();
    });
  });

  group('Readiness', () {
    // Reached only via Progress's Recovery segment — see
    // readiness_home_screen_test.dart's own doc comment for why Readiness
    // has no bottom tab of its own.
    Future<void> pumpToReadinessHome(WidgetTester tester) async {
      await _pumpApp(tester);
      await tester.tap(find.text('Progress').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Recovery'));
      await tester.pumpAndSettle();
      await _scrollToAndTap(tester, find.text('Readiness check-ins'));
    }

    testWidgets('Readiness Home meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await pumpToReadinessHome(tester);

      expect(find.text('Readiness'), findsWidgets); // AppBar title
      await _checkGuideline(tester);

      handle.dispose();
    });

    testWidgets('Readiness Check-in meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await pumpToReadinessHome(tester);
      await _scrollToAndTap(tester, find.text('Start check-in'));

      expect(find.text('Readiness check-in'), findsOneWidget);
      await _checkGuideline(tester);

      handle.dispose();
    });

    testWidgets('Recovery Timeline meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await pumpToReadinessHome(tester);
      await tester.tap(find.text('See all'));
      await tester.pumpAndSettle();

      expect(find.text('Recovery timeline'), findsOneWidget);
      await _checkGuideline(tester);

      handle.dispose();
    });

    testWidgets('Check-in Detail meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await pumpToReadinessHome(tester);
      await tester.tap(find.byType(ReadinessEntryTile).first);
      await tester.pumpAndSettle();

      expect(find.text('Check-in detail'), findsOneWidget);
      await _checkGuideline(tester);

      handle.dispose();
    });

    testWidgets('Recovery Score (formula) meets Android tap-target and text-contrast '
        'guidelines', (tester) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await pumpToReadinessHome(tester);
      await _scrollToAndTap(tester, find.text('Recovery score'));

      expect(find.text('Recovery score not connected yet'), findsOneWidget);
      await _checkGuideline(tester);

      handle.dispose();
    });
  });

  group('Coach', () {
    testWidgets('Weekly Review meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await _pumpApp(tester);
      await tester.tap(find.text('Coach').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Weekly review'));
      await tester.pumpAndSettle();

      expect(find.text('Weekly review not connected yet'), findsOneWidget);
      await _checkGuideline(tester);

      handle.dispose();
    });

    testWidgets('Coaching History meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await _pumpApp(tester);
      await tester.tap(find.text('Coach').last);
      await tester.pumpAndSettle();
      await _scrollToAndTap(tester, find.text('Coaching history'));

      expect(find.text('Coaching history not connected yet'), findsOneWidget);
      await _checkGuideline(tester);

      handle.dispose();
    });

    testWidgets('Guidance Detail meets Android tap-target and text-contrast guidelines', (
      tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      final CoachSignal signal = CoachSignal(
        id: 's1',
        module: CoachModule.recovery,
        severity: CoachSeverity.warning,
        message: 'Sleep has been below target.',
        occurredAt: DateTime.now(),
      );
      await tester.pumpWidget(
        ProviderScope(
          overrides: <Override>[
            ...authenticatedTestOverrides(),
            todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
            trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
            fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
            progressRepositoryProvider.overrideWithValue(MockProgressRepository()),
            readinessRepositoryProvider.overrideWithValue(MockReadinessRepository()),
            coachRepositoryProvider.overrideWithValue(_FixedCoachRepository(<CoachSignal>[signal])),
          ],
          child: const GymCompanionApp(),
        ),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text('Coach').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Sleep has been below target.'));
      await tester.pumpAndSettle();

      expect(find.text('Guidance detail'), findsOneWidget);
      await _checkGuideline(tester);

      handle.dispose();
    });
  });
}

class _FixedCoachRepository implements CoachRepository {
  const _FixedCoachRepository(this.signals);

  final List<CoachSignal> signals;

  @override
  Future<List<CoachSignal>> fetchRecentSignals() async => signals;
}
