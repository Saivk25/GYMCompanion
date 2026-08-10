import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/app.dart';
import 'package:gym_companion_mobile/design/design.dart';
import 'package:gym_companion_mobile/features/coach/application/coach_controller.dart';
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
import 'package:gym_companion_mobile/shared/domain/coach_signal.dart';
import '../../support/auth_test_overrides.dart';

/// A controllable fake — mirrors `_FakeReadinessRepository`'s own
/// reasoning (`readiness_home_screen_test.dart`): [fetchRecentSignals]
/// resolves only once [complete] is called, so a test can observe the
/// loading state before resolving.
class _FakeCoachRepository implements CoachRepository {
  _FakeCoachRepository(this.next);

  final List<CoachSignal> next;
  final Completer<List<CoachSignal>> _completer = Completer<List<CoachSignal>>();

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
  Future<List<CoachSignal>> fetchRecentSignals() => _completer.future;
}

Future<void> _pumpCoach(WidgetTester tester, List<CoachSignal> signals) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: <Override>[
        ...authenticatedTestOverrides(),
        todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
        trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
        fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
        progressRepositoryProvider.overrideWithValue(MockProgressRepository()),
        readinessRepositoryProvider.overrideWithValue(MockReadinessRepository()),
        coachRepositoryProvider.overrideWithValue(_FakeCoachRepository(signals)..complete()),
      ],
      child: const GymCompanionApp(),
    ),
  );
  await tester.pumpAndSettle();
  await tester.tap(find.text('Coach').last);
  await tester.pumpAndSettle();
}

CoachSignal _signal({
  required String id,
  required CoachModule module,
  CoachSeverity severity = CoachSeverity.advisory,
  String message = 'Example guidance message.',
}) {
  return CoachSignal(
    id: id,
    module: module,
    severity: severity,
    message: message,
    occurredAt: DateTime.now(),
  );
}

void main() {
  testWidgets('shows a skeleton, never a spinner, while the first fetch is pending', (
    tester,
  ) async {
    final _FakeCoachRepository repo = _FakeCoachRepository(const <CoachSignal>[]);
    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
        ...authenticatedTestOverrides(),
          todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
          trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
          fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
          progressRepositoryProvider.overrideWithValue(MockProgressRepository()),
          readinessRepositoryProvider.overrideWithValue(MockReadinessRepository()),
          coachRepositoryProvider.overrideWithValue(repo),
        ],
        child: const GymCompanionApp(),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Coach').last);
    await tester.pump();

    expect(find.byType(AppSkeletonBox), findsWidgets);
    expect(find.byType(CircularProgressIndicator), findsNothing);

    repo.complete();
    await tester.pumpAndSettle();
  });

  testWidgets('a brand-new session with no captured signals shows the honest empty state', (
    tester,
  ) async {
    await _pumpCoach(tester, const <CoachSignal>[]);

    expect(find.text('Nothing to show yet'), findsOneWidget);
  });

  testWidgets('always explains itself as rule-based, never AI or chat', (tester) async {
    await _pumpCoach(tester, const <CoachSignal>[]);

    expect(find.text('How this works'), findsOneWidget);
    expect(find.textContaining('not a chat assistant'), findsOneWidget);
  });

  testWidgets('real captured signals render in the feed with their real module and severity', (
    tester,
  ) async {
    await _pumpCoach(tester, <CoachSignal>[
      _signal(
        id: 's1',
        module: CoachModule.recovery,
        severity: CoachSeverity.warning,
        message: 'Sleep has been below target.',
      ),
    ]);

    expect(find.text('Sleep has been below target.'), findsOneWidget);
    expect(find.textContaining('Recovery'), findsWidgets);
  });

  testWidgets('the module filter narrows the feed to real signals from that module only', (
    tester,
  ) async {
    await _pumpCoach(tester, <CoachSignal>[
      _signal(id: 's1', module: CoachModule.recovery, message: 'Recovery message'),
      _signal(id: 's2', module: CoachModule.nutrition, message: 'Nutrition message'),
    ]);

    expect(find.text('Recovery message'), findsOneWidget);
    expect(find.text('Nutrition message'), findsOneWidget);

    await tester.tap(find.text('Nutrition').last);
    await tester.pumpAndSettle();

    expect(find.text('Recovery message'), findsNothing);
    expect(find.text('Nutrition message'), findsOneWidget);
  });

  testWidgets('tapping "Weekly review" is a real, reachable, honest placeholder', (tester) async {
    await _pumpCoach(tester, const <CoachSignal>[]);

    await tester.tap(find.text('Weekly review'));
    await tester.pumpAndSettle();

    expect(find.text('Weekly review not connected yet'), findsOneWidget);
  });

  testWidgets('tapping "Coaching history" is a real, reachable, honest placeholder', (
    tester,
  ) async {
    await _pumpCoach(tester, const <CoachSignal>[]);

    await tester.tap(find.text('Coaching history'));
    await tester.pumpAndSettle();

    expect(find.text('Coaching history not connected yet'), findsOneWidget);
  });

  testWidgets('tapping a signal opens its real detail — full message, module, '
      'severity, and a plain-language sourcing disclosure', (tester) async {
    await _pumpCoach(tester, <CoachSignal>[
      _signal(
        id: 's1',
        module: CoachModule.recovery,
        severity: CoachSeverity.warning,
        message: 'Sleep has been below target.',
      ),
    ]);

    await tester.tap(find.text('Sleep has been below target.'));
    await tester.pumpAndSettle();

    expect(find.text('Guidance detail'), findsOneWidget); // AppBar title
    // Coach Home's own route stays mounted underneath this pushed one
    // (the same reason `checkin_flow_test.dart`'s "See all" test uses
    // `findsWidgets`, not `findsOneWidget`, for text that also appears
    // on the screen beneath), so the message matches both the still-
    // present feed tile and this detail screen's own repeated text.
    expect(find.text('Sleep has been below target.'), findsWidgets);
    expect(find.textContaining('Recovery'), findsWidgets);
    expect(
      find.textContaining('a real, deterministic rule check on the backend'),
      findsOneWidget,
    );
  });

  testWidgets('a genuine page fetch failure offers retry, not a silent blank screen', (
    tester,
  ) async {
    final _FakeCoachRepository repo = _FakeCoachRepository(const <CoachSignal>[]);
    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
        ...authenticatedTestOverrides(),
          todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
          trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
          fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
          progressRepositoryProvider.overrideWithValue(MockProgressRepository()),
          readinessRepositoryProvider.overrideWithValue(MockReadinessRepository()),
          coachRepositoryProvider.overrideWithValue(repo),
        ],
        child: const GymCompanionApp(),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Coach').last);
    repo.completeWithError();
    await tester.pumpAndSettle();

    expect(find.text("Coach couldn't be loaded."), findsOneWidget);
    expect(find.text('Try again'), findsOneWidget);
  });
}
