import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/design/design.dart';
import 'package:gym_companion_mobile/features/today/application/today_controller.dart';
import 'package:gym_companion_mobile/features/today/domain/today_models.dart';
import 'package:gym_companion_mobile/features/today/presentation/today_screen.dart';

/// A controllable fake — unlike [MockTodayRepository]'s fixed 300ms
/// delay, this resolves to whatever [next] is set to, only once
/// [complete] is called, so tests can observe the loading state and
/// assert on it before resolving.
class _FakeTodayRepository implements TodayRepository {
  _FakeTodayRepository(this.next);

  final TodayViewState next;
  final Completer<TodayViewState> _completer = Completer<TodayViewState>();

  void complete() {
    if (!_completer.isCompleted) {
      _completer.complete(next);
    }
  }

  @override
  Future<TodayViewState> fetchToday() => _completer.future;
}

TodayViewState _baseState({
  bool hasActivePlan = true,
  ReadinessBand readinessBand = ReadinessBand.normal,
  bool checkInCompletedToday = true,
  SessionCardStatus sessionStatus = SessionCardStatus.ready,
  TodaySessionSummary? session,
  TodayStreak? streak,
  TodayTask? task,
  bool isOffline = false,
}) {
  return TodayViewState(
    date: DateTime(2026, 8, 4),
    hasActivePlan: hasActivePlan,
    readinessBand: readinessBand,
    checkInCompletedToday: checkInCompletedToday,
    sessionStatus: sessionStatus,
    session: session ??
        TodaySessionSummary(
          workoutId: 'workout-today',
          name: 'Upper Body Strength',
          plannedDate: DateTime(2026, 8, 4),
        ),
    streak: streak,
    task: task,
    isOffline: isOffline,
  );
}

Future<void> _pumpToday(WidgetTester tester, TodayViewState state) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: <Override>[
        todayRepositoryProvider
            .overrideWithValue(_FakeTodayRepository(state)..complete()),
      ],
      child: MaterialApp(theme: AppTheme.light, home: const Scaffold(body: TodayScreen())),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('shows a skeleton, never a spinner, while the first fetch is pending', (
    tester,
  ) async {
    final _FakeTodayRepository repo = _FakeTodayRepository(_baseState());
    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[todayRepositoryProvider.overrideWithValue(repo)],
        child: MaterialApp(theme: AppTheme.light, home: const Scaffold(body: TodayScreen())),
      ),
    );
    await tester.pump();

    expect(find.byType(AppSkeletonBox), findsWidgets);
    expect(find.byType(CircularProgressIndicator), findsNothing);

    repo.complete();
    await tester.pumpAndSettle();
  });

  testWidgets('a ready session shows the Start session action', (tester) async {
    await _pumpToday(tester, _baseState());

    expect(find.text('Start session'), findsOneWidget);
    expect(find.text("Today's readiness check-in"), findsNothing);
  });

  testWidgets(
    'an outstanding check-in outranks the session card, appearing above it',
    (tester) async {
      await _pumpToday(tester, _baseState(checkInCompletedToday: false));

      expect(find.text("Today's readiness check-in"), findsOneWidget);
      expect(find.text('Start session'), findsOneWidget);

      final double checkInY =
          tester.getTopLeft(find.text("Today's readiness check-in")).dy;
      final double sessionY = tester.getTopLeft(find.text("Today's session")).dy;
      expect(checkInY, lessThan(sessionY));
    },
  );

  testWidgets('a completed session shows "Done for today" and keeps the '
      'two-minute-win action visible', (tester) async {
    await _pumpToday(
      tester,
      _baseState(sessionStatus: SessionCardStatus.completed),
    );

    expect(find.text('Done for today'), findsOneWidget);
    expect(find.text('Log a 2-minute win for tomorrow'), findsOneWidget);
  });

  testWidgets('no active plan shows the onboarding-continuation card, not '
      'a session card', (tester) async {
    await _pumpToday(
      tester,
      _baseState(hasActivePlan: false, sessionStatus: SessionCardStatus.empty),
    );

    expect(find.text("Let's build your first plan"), findsOneWidget);
    expect(find.text('Start session'), findsNothing);
  });

  testWidgets('a session-generation failure offers "Browse exercise '
      'library", not a blocking full-screen error', (tester) async {
    await _pumpToday(
      tester,
      _baseState(sessionStatus: SessionCardStatus.error),
    );

    expect(find.text('Browse exercise library'), findsOneWidget);
    // The rest of the page — here, the readiness band chip — still
    // renders; a session failure must not blank the whole screen.
    expect(find.text('Normal'), findsOneWidget);
  });

  testWidgets('an open task renders with its rationale and action', (tester) async {
    await _pumpToday(
      tester,
      _baseState(
        task: const TodayTask(
          text: 'Your bench press has stalled.',
          actionLabel: 'Review',
          rationale: 'Based on your last 3 sessions.',
        ),
      ),
    );

    expect(find.text('Your bench press has stalled.'), findsOneWidget);
    expect(find.text('Based on your last 3 sessions.'), findsOneWidget);
    expect(find.text('Review'), findsOneWidget);
  });

  testWidgets('offline shows a small inline indicator, not a banner', (tester) async {
    await _pumpToday(tester, _baseState(isOffline: true));

    expect(find.textContaining('Offline'), findsOneWidget);
  });

  testWidgets('the streak renders as plain text, never a badge', (tester) async {
    await _pumpToday(
      tester,
      _baseState(streak: const TodayStreak(currentDays: 12, graceUsed: false)),
    );

    expect(find.text('12-day streak'), findsOneWidget);
  });
}
