import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/app.dart';
import 'package:gym_companion_mobile/core/cache/cache.dart';
import 'package:gym_companion_mobile/features/auth/application/auth_controller.dart';
import 'package:gym_companion_mobile/features/auth/infrastructure/mock_auth_repository.dart';
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
import 'package:shared_preferences/shared_preferences.dart';

/// End-to-end through the real router (`lib/shell/app_router.dart`'s
/// `routerProvider`) and the real [AuthController] — proving the
/// actual guard/redirect wiring this phase's own architecture depends
/// on, not just each piece in isolation. Mirrors the reasoning every
/// other module's own `*_flow_test.dart` gives for testing this way
/// (e.g. `checkin_flow_test.dart`, `coach_signal_flow_test.dart`).
List<Override> _featureRepositoryOverrides() => <Override>[
      todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
      trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
      fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
      progressRepositoryProvider.overrideWithValue(MockProgressRepository()),
      readinessRepositoryProvider.overrideWithValue(MockReadinessRepository()),
      coachRepositoryProvider.overrideWith(
        (ref) => MockCoachRepository(() => ref.read(coachSignalLogProvider)),
      ),
    ];

/// `AuthController._clearLocalSession` now also clears the shared
/// [LocalCache] (`docs/adr/0052-offline-caching.md`), and the "logging
/// out from the top bar" test below exercises that real path — every
/// pump helper here needs a real (mocked) [SharedPreferences] instance
/// behind [localCacheProvider], the same `setMockInitialValues` pattern
/// `test/features/auth/auth_controller_test.dart` uses.
Future<SharedPreferences> _mockSharedPreferences() async {
  SharedPreferences.setMockInitialValues(<String, Object>{});
  return SharedPreferences.getInstance();
}

Future<void> _pumpUnauthenticatedApp(WidgetTester tester) async {
  final SharedPreferences prefs = await _mockSharedPreferences();
  await tester.pumpWidget(
    ProviderScope(
      overrides: <Override>[
        ..._featureRepositoryOverrides(),
        authRepositoryProvider.overrideWithValue(const MockAuthRepository()),
        tokenStorageProvider.overrideWithValue(MockTokenStorage(seedRefreshToken: null)),
        localCacheProvider.overrideWithValue(LocalCache(prefs)),
      ],
      child: const GymCompanionApp(),
    ),
  );
  await tester.pumpAndSettle();
}

Future<void> _pumpAuthenticatedApp(WidgetTester tester) async {
  final SharedPreferences prefs = await _mockSharedPreferences();
  await tester.pumpWidget(
    ProviderScope(
      overrides: <Override>[
        ..._featureRepositoryOverrides(),
        authRepositoryProvider.overrideWithValue(const MockAuthRepository()),
        tokenStorageProvider.overrideWithValue(MockTokenStorage()),
        localCacheProvider.overrideWithValue(LocalCache(prefs)),
      ],
      child: const GymCompanionApp(),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('a signed-out session lands on Login, never on Today', (tester) async {
    await _pumpUnauthenticatedApp(tester);

    expect(find.text('Sign in to continue'), findsOneWidget);
    expect(find.text('Nothing planned this week'), findsNothing);
  });

  testWidgets('a signed-in session lands directly on Today, no Login screen flash', (
    tester,
  ) async {
    await _pumpAuthenticatedApp(tester);

    expect(find.text('Sign in to continue'), findsNothing);
    // Today's own bottom-tab label proves the shell (five tabs) rendered.
    expect(find.text('Today').first, findsOneWidget);
  });

  testWidgets('a real login submit redirects to Today — the router reacts to '
      'AuthController state, not an explicit navigation call', (tester) async {
    await _pumpUnauthenticatedApp(tester);

    await tester.enterText(find.byType(TextField).first, 'member@example.com');
    await tester.enterText(find.byType(TextField).last, 'correct-horse-battery-staple');
    await tester.tap(find.text('Sign in'));
    await tester.pumpAndSettle();

    expect(find.text('Sign in to continue'), findsNothing);
    expect(find.text('Today').first, findsOneWidget);
  });

  testWidgets('"Create one" reaches the real Register screen', (tester) async {
    await _pumpUnauthenticatedApp(tester);

    await tester.tap(find.text("Don't have an account? Create one"));
    await tester.pumpAndSettle();

    expect(find.text('Create account'), findsOneWidget);
  });

  testWidgets('a real registration submit also redirects to Today', (tester) async {
    await _pumpUnauthenticatedApp(tester);
    await tester.tap(find.text("Don't have an account? Create one"));
    await tester.pumpAndSettle();

    final Finder fields = find.byType(TextField);
    await tester.enterText(fields.at(0), 'new@example.com');
    await tester.enterText(fields.at(1), 'a-strong-password');
    await tester.enterText(fields.at(2), 'a-strong-password');
    await tester.tap(find.text('Create account'));
    await tester.pumpAndSettle();

    expect(find.text('Today').first, findsOneWidget);
  });

  testWidgets('mismatched passwords on Register show a local error and never call the backend',
      (tester) async {
    await _pumpUnauthenticatedApp(tester);
    await tester.tap(find.text("Don't have an account? Create one"));
    await tester.pumpAndSettle();

    final Finder fields = find.byType(TextField);
    await tester.enterText(fields.at(0), 'new@example.com');
    await tester.enterText(fields.at(1), 'password-one');
    await tester.enterText(fields.at(2), 'password-two');
    await tester.tap(find.text('Create account'));
    await tester.pumpAndSettle();

    expect(find.text('Passwords do not match.'), findsOneWidget);
    // Still on Register — a local validation failure never reaches
    // AuthController/the backend at all.
    expect(find.text('Create account'), findsOneWidget);
  });

  testWidgets('logging out from the top bar returns to Login', (tester) async {
    await _pumpAuthenticatedApp(tester);
    expect(find.text('Today').first, findsOneWidget);

    await tester.tap(find.byTooltip('Log out'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Log out').last);
    await tester.pumpAndSettle();

    expect(find.text('Sign in to continue'), findsOneWidget);
  });
}
