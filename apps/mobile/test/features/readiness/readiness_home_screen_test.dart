import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/app.dart';
import 'package:gym_companion_mobile/design/design.dart';
import 'package:gym_companion_mobile/features/coach/application/coach_controller.dart';
import 'package:gym_companion_mobile/features/coach/infrastructure/mock_coach_repository.dart';
import 'package:gym_companion_mobile/features/fuel/application/fuel_controller.dart';
import 'package:gym_companion_mobile/features/fuel/infrastructure/mock_fuel_repository.dart';
import 'package:gym_companion_mobile/features/progress/application/progress_controller.dart';
import 'package:gym_companion_mobile/features/progress/infrastructure/mock_progress_repository.dart';
import 'package:gym_companion_mobile/features/readiness/application/readiness_controller.dart';
import 'package:gym_companion_mobile/features/readiness/domain/readiness_models.dart';
import 'package:gym_companion_mobile/features/today/application/today_controller.dart';
import 'package:gym_companion_mobile/features/today/infrastructure/mock_today_repository.dart';
import 'package:gym_companion_mobile/features/train/application/train_controller.dart';
import 'package:gym_companion_mobile/features/train/infrastructure/mock_train_repository.dart';
import 'package:gym_companion_mobile/shared/application/coach_signal_log.dart';
import '../../support/auth_test_overrides.dart';

/// A controllable fake — mirrors `_FakeProgressRepository`'s own
/// reasoning (`progress_home_screen_test.dart`): [fetchHome] resolves
/// only once [complete] is called. [submitCheckIn] throws — Readiness
/// Home's own tests never call it; the check-in flow itself is covered
/// end-to-end in `checkin_flow_test.dart` against the real
/// `MockReadinessRepository`.
class _FakeReadinessRepository implements ReadinessRepository {
  _FakeReadinessRepository(this.next);

  final ReadinessHomeViewState next;
  final Completer<ReadinessHomeViewState> _completer = Completer<ReadinessHomeViewState>();

  void complete() {
    if (!_completer.isCompleted) {
      _completer.complete(next);
    }
  }

  void completeWithError() {
    if (!_completer.isCompleted) {
      _completer.completeError(StateError('fetch failed'));
    }
  }

  @override
  Future<ReadinessHomeViewState> fetchHome() => _completer.future;

  @override
  Future<ReadinessCheckInResult> submitCheckIn({
    required DateTime date,
    Duration? sleepDuration,
    int? sleepQuality,
    int? energyLevel,
    int? stressLevel,
    int? sorenessLevel,
    double? restingHeartRate,
    double? heartRateVariability,
    String? notes,
  }) =>
      throw UnimplementedError();
}

/// Readiness has no bottom tab of its own — every test reaches it via
/// Progress's Recovery segment's "Readiness check-ins" link (the same
/// root-navigator push `docs/adr/0040-readiness-module.md` documents).
/// `MockProgressRepository`'s default seed carries real recovery-week
/// data, so the "Readiness check-ins" row is always reachable without
/// hand-building a `ProgressHomeViewState`.
Future<void> _pumpToReadinessHome(WidgetTester tester, ReadinessHomeViewState state) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: <Override>[
        ...authenticatedTestOverrides(),
        todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
        trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
        fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
        progressRepositoryProvider.overrideWithValue(MockProgressRepository()),
        readinessRepositoryProvider.overrideWithValue(_FakeReadinessRepository(state)..complete()),
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
  await tester.tap(find.text('Readiness check-ins'));
  await tester.pumpAndSettle();
}

ReadinessEntry _entry({
  required String id,
  required DateTime date,
  Duration? sleepDuration,
  int? sleepQuality,
  int? energyLevel,
  int? stressLevel,
  int? sorenessLevel,
  double? restingHeartRate,
  double? heartRateVariability,
}) {
  return ReadinessEntry(
    readinessId: id,
    readinessDate: date,
    recordedAt: date,
    source: ReadinessSource.manual,
    sleepDuration: sleepDuration,
    sleepQuality: sleepQuality,
    energyLevel: energyLevel,
    stressLevel: stressLevel,
    sorenessLevel: sorenessLevel,
    restingHeartRate: restingHeartRate,
    heartRateVariability: heartRateVariability,
  );
}

void main() {
  testWidgets('shows a skeleton, never a spinner, while the first fetch is pending', (
    tester,
  ) async {
    final _FakeReadinessRepository repo = _FakeReadinessRepository(
      ReadinessHomeViewState(asOf: DateTime.now(), hasCheckedInEver: false),
    );
    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
        ...authenticatedTestOverrides(),
          todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
          trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
          fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
          progressRepositoryProvider.overrideWithValue(MockProgressRepository()),
          readinessRepositoryProvider.overrideWithValue(repo),
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
    await tester.tap(find.text('Readiness check-ins'));
    await tester.pump();

    expect(find.byType(AppSkeletonBox), findsWidgets);
    expect(find.byType(CircularProgressIndicator), findsNothing);

    repo.complete();
    await tester.pumpAndSettle();
  });

  testWidgets('a brand-new user with no history ever sees the first-check-in empty state', (
    tester,
  ) async {
    await _pumpToReadinessHome(
      tester,
      ReadinessHomeViewState(asOf: DateTime.now(), hasCheckedInEver: false),
    );

    expect(find.text('Log your first check-in'), findsOneWidget);
  });

  testWidgets('a returning user who has not checked in today sees the start prompt', (
    tester,
  ) async {
    await _pumpToReadinessHome(
      tester,
      ReadinessHomeViewState(
        asOf: DateTime.now(),
        entries: <ReadinessEntry>[
          _entry(id: 'r1', date: DateTime.now().subtract(const Duration(days: 1)), energyLevel: 6),
        ],
      ),
    );

    expect(find.text("You haven't checked in today yet."), findsOneWidget);
  });

  testWidgets('a completed check-in today shows real recorded values, never a computed score', (
    tester,
  ) async {
    await _pumpToReadinessHome(
      tester,
      ReadinessHomeViewState(
        asOf: DateTime.now(),
        entries: <ReadinessEntry>[
          _entry(
            id: 'r-today',
            date: DateTime.now(),
            sleepDuration: const Duration(hours: 7, minutes: 30),
            sleepQuality: 7,
            energyLevel: 6,
            stressLevel: 4,
            sorenessLevel: 3,
            restingHeartRate: 55,
            heartRateVariability: 60,
          ),
        ],
      ),
    );

    expect(find.text("Today's check-in"), findsOneWidget);
    expect(find.text('7.5h'), findsOneWidget);
    expect(find.text('6/10'), findsOneWidget);
    expect(find.text('55 bpm'), findsOneWidget);
    expect(find.text('60 ms'), findsOneWidget);
  });

  testWidgets('real advisory warnings from the last submission render as plain text', (
    tester,
  ) async {
    await _pumpToReadinessHome(
      tester,
      ReadinessHomeViewState(
        asOf: DateTime.now(),
        entries: <ReadinessEntry>[_entry(id: 'r-today', date: DateTime.now(), energyLevel: 3)],
        lastCheckInWarnings: const <String>['[warning] Example advisory text.'],
      ),
    );

    expect(find.text('Advisory notes from your last check-in'), findsOneWidget);
    expect(find.text('[warning] Example advisory text.'), findsOneWidget);
  });

  testWidgets('recent check-ins render in the preview list', (tester) async {
    await _pumpToReadinessHome(
      tester,
      ReadinessHomeViewState(
        asOf: DateTime.now(),
        entries: <ReadinessEntry>[
          _entry(id: 'r1', date: DateTime.now(), sleepDuration: const Duration(hours: 7)),
          _entry(
            id: 'r2',
            date: DateTime.now().subtract(const Duration(days: 1)),
            energyLevel: 5,
          ),
        ],
      ),
    );

    expect(find.text('Recent check-ins'), findsOneWidget);
  });

  testWidgets('the recovery score entry point is an honest, reachable placeholder', (
    tester,
  ) async {
    await _pumpToReadinessHome(
      tester,
      ReadinessHomeViewState(
        asOf: DateTime.now(),
        entries: <ReadinessEntry>[_entry(id: 'r1', date: DateTime.now(), energyLevel: 6)],
      ),
    );

    await tester.tap(find.text('Recovery score'));
    await tester.pumpAndSettle();

    expect(find.text('Recovery score not connected yet'), findsOneWidget);
  });

  testWidgets('a genuine page fetch failure offers retry, not a silent blank screen', (
    tester,
  ) async {
    final _FakeReadinessRepository repo = _FakeReadinessRepository(
      ReadinessHomeViewState(asOf: DateTime.now(), hasCheckedInEver: false),
    );
    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
        ...authenticatedTestOverrides(),
          todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
          trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
          fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
          progressRepositoryProvider.overrideWithValue(MockProgressRepository()),
          readinessRepositoryProvider.overrideWithValue(repo),
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
    await tester.tap(find.text('Readiness check-ins'));
    repo.completeWithError();
    await tester.pumpAndSettle();

    expect(find.text("Readiness couldn't be loaded."), findsOneWidget);
    expect(find.text('Try again'), findsOneWidget);
  });

  testWidgets('offline shows a small inline indicator, not a banner', (tester) async {
    await _pumpToReadinessHome(
      tester,
      ReadinessHomeViewState(
        asOf: DateTime.now(),
        entries: <ReadinessEntry>[_entry(id: 'r1', date: DateTime.now(), energyLevel: 6)],
        isOffline: true,
      ),
    );

    expect(find.textContaining('Offline'), findsOneWidget);
  });
}
