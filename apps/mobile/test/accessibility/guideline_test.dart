import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/design/design.dart';
import 'package:gym_companion_mobile/features/coach/application/coach_controller.dart';
import 'package:gym_companion_mobile/features/coach/infrastructure/mock_coach_repository.dart';
import 'package:gym_companion_mobile/features/coach/presentation/coach_home_screen.dart';
import 'package:gym_companion_mobile/features/today/application/today_controller.dart';
import 'package:gym_companion_mobile/features/today/infrastructure/mock_today_repository.dart';
import 'package:gym_companion_mobile/features/today/presentation/today_screen.dart';
import 'package:gym_companion_mobile/shared/application/coach_signal_log.dart';
import 'package:gym_companion_mobile/shared/domain/coach_signal.dart';

/// The automatable subset of `docs/adr/0042-production-integration-
/// plan.md` Part 5/Part 6's own accessibility findings —
/// `flutter_test`'s built-in `meetsGuideline` matchers, which need only
/// the widget-test harness (no real device/TalkBack/VoiceOver, unlike
/// the rest of Part 5's findings — see `docs/adr/0002`'s own standing
/// constraint). Run against two real, representative screens rather
/// than every screen in the app: Today (the landing screen every user
/// sees first) and Coach Home (the most visually varied composed
/// screen — badges, filter chips, and list tiles together, exactly the
/// combination ADR 0042 Part 5 flagged as unverified "components that
/// individually pass now laid out next to each other"). This is a
/// representative sample demonstrating the check now exists and passes,
/// not a claim that every screen has been swept — see
/// `docs/adr/0035-design-system-refinement.md` for the component-level
/// contrast/touch-target work this builds on.
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

    await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
    await expectLater(tester, meetsGuideline(textContrastGuideline));

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

    await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
    await expectLater(tester, meetsGuideline(textContrastGuideline));

    handle.dispose();
  });
}

class _FixedCoachRepository implements CoachRepository {
  const _FixedCoachRepository(this.signals);

  final List<CoachSignal> signals;

  @override
  Future<List<CoachSignal>> fetchRecentSignals() async => signals;
}
