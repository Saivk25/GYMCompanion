import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/shared/application/coach_signal_log.dart';
import 'package:gym_companion_mobile/shared/domain/coach_signal.dart';

void main() {
  group('CoachSignal.parse', () {
    test('parses the real "[severity] message" shape advisory_warnings() produces', () {
      final CoachSignal signal = CoachSignal.parse(
        id: 's1',
        module: CoachModule.recovery,
        raw: '[warning] Sleep has been below target for 3 days.',
        occurredAt: DateTime(2026, 1, 1),
      );

      expect(signal.severity, CoachSeverity.warning);
      expect(signal.message, 'Sleep has been below target for 3 days.');
      expect(signal.module, CoachModule.recovery);
    });

    test('recognizes every real backend severity token', () {
      for (final (String token, CoachSeverity expected) in <(String, CoachSeverity)>[
        ('info', CoachSeverity.info),
        ('advisory', CoachSeverity.advisory),
        ('warning', CoachSeverity.warning),
        ('critical', CoachSeverity.critical),
      ]) {
        final CoachSignal signal = CoachSignal.parse(
          id: 's1',
          module: CoachModule.training,
          raw: '[$token] message text',
          occurredAt: DateTime(2026, 1, 1),
        );
        expect(signal.severity, expected, reason: 'token "$token"');
      }
    });

    test('degrades a malformed string to info, keeping the whole string as the message', () {
      final CoachSignal signal = CoachSignal.parse(
        id: 's1',
        module: CoachModule.nutrition,
        raw: 'no bracket prefix here',
        occurredAt: DateTime(2026, 1, 1),
      );

      expect(signal.severity, CoachSeverity.info);
      expect(signal.message, 'no bracket prefix here');
    });
  });

  group('CoachSignalLog', () {
    test('starts empty', () {
      final ProviderContainer container = ProviderContainer();
      addTearDown(container.dispose);

      expect(container.read(coachSignalLogProvider), isEmpty);
    });

    test('an empty warnings list is a no-op, not a fabricated signal', () {
      final ProviderContainer container = ProviderContainer();
      addTearDown(container.dispose);

      container.read(coachSignalLogProvider.notifier).add(CoachModule.recovery, const <String>[]);

      expect(container.read(coachSignalLogProvider), isEmpty);
    });

    test('adds real warnings, newest first', () {
      final ProviderContainer container = ProviderContainer();
      addTearDown(container.dispose);
      final CoachSignalLog notifier = container.read(coachSignalLogProvider.notifier);

      notifier.add(CoachModule.recovery, const <String>['[warning] first batch, item one']);
      notifier.add(CoachModule.nutrition, const <String>['[info] second batch, item one']);

      final List<CoachSignal> signals = container.read(coachSignalLogProvider);
      expect(signals, hasLength(2));
      // Newest batch first.
      expect(signals.first.module, CoachModule.nutrition);
      expect(signals.first.message, 'second batch, item one');
      expect(signals.last.module, CoachModule.recovery);
    });

    test('a single call with multiple warnings preserves their relative order within the batch', () {
      final ProviderContainer container = ProviderContainer();
      addTearDown(container.dispose);
      final CoachSignalLog notifier = container.read(coachSignalLogProvider.notifier);

      notifier.add(CoachModule.training, const <String>[
        '[advisory] first message',
        '[warning] second message',
      ]);

      final List<CoachSignal> signals = container.read(coachSignalLogProvider);
      expect(signals, hasLength(2));
      expect(signals[0].message, 'first message');
      expect(signals[1].message, 'second message');
    });
  });
}
