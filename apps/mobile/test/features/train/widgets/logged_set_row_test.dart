import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/design/design.dart';
import 'package:gym_companion_mobile/features/train/domain/train_models.dart';
import 'package:gym_companion_mobile/features/train/presentation/widgets/logged_set_row.dart';

/// Regression test for TD-0012 (`docs/TECH_DEBT.md`) — the "Mark
/// complete" `InkWell`'s own hit area, not just the row it sits in, must
/// genuinely reach the 48dp minimum touch target this design system
/// enforces everywhere else (`docs/adr/0035`).
void main() {
  const TrainExerciseSet incompleteSet = TrainExerciseSet(
    setNumber: 1,
    weight: 60,
    reps: 8,
    rpe: 7,
    completed: false,
  );

  testWidgets(
    "an incomplete set's Mark complete InkWell itself meets the 48dp minimum touch target",
    (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.light,
          home: Scaffold(
            body: LoggedSetRow(set: incompleteSet, onComplete: () {}),
          ),
        ),
      );

      final Size size = tester.getSize(find.byType(InkWell));
      expect(size.width, greaterThanOrEqualTo(kMinInteractiveDimension));
      expect(size.height, greaterThanOrEqualTo(kMinInteractiveDimension));
    },
  );

  testWidgets(
    'tapping the Mark complete affordance invokes onComplete',
    (WidgetTester tester) async {
      int tapCount = 0;
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.light,
          home: Scaffold(
            body: LoggedSetRow(
              set: incompleteSet,
              onComplete: () => tapCount++,
            ),
          ),
        ),
      );

      await tester.tap(find.text('Mark complete'));
      await tester.pump();

      expect(tapCount, 1);
    },
  );
}
