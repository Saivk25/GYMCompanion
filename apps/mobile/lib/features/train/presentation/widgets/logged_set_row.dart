import 'package:flutter/material.dart';

import '../../../../design/design.dart';
import '../../domain/train_models.dart';

/// One already-logged set — a compact row, not a card, since a session
/// can have many of these stacked per exercise. A logged-but-not-yet-
/// confirmed set (`completed: false`, the real two-step backend flow —
/// see `train_models.dart`'s own doc comment) shows a tappable "Mark
/// complete" affordance; a confirmed one shows a quiet checkmark, no
/// further action.
class LoggedSetRow extends StatelessWidget {
  const LoggedSetRow({required this.set, required this.onComplete, super.key});

  final TrainExerciseSet set;
  final VoidCallback onComplete;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final AppSemanticColors semantic = Theme.of(context).semanticColors;

    return ConstrainedBox(
      constraints: const BoxConstraints(minHeight: kMinInteractiveDimension),
      child: Row(
        children: <Widget>[
          SizedBox(
            width: 28,
            child: Text('${set.setNumber}', style: textTheme.bodyMedium),
          ),
          Expanded(
            child: Text(
              '${set.weight.toStringAsFixed(0)} × ${set.reps} @ RPE ${set.rpe}',
              style: textTheme.bodyMedium,
            ),
          ),
          if (set.completed)
            Icon(AppIcons.successFilled, color: semantic.success, size: 20)
          else
            Semantics(
              button: true,
              label: 'Mark set ${set.setNumber} complete',
              child: InkWell(
                onTap: onComplete,
                borderRadius: AppRadius.radiusSm,
                child: Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.sm,
                    vertical: AppSpacing.xs,
                  ),
                  child: Text(
                    'Mark complete',
                    style: textTheme.labelMedium?.copyWith(color: colorScheme.primary),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
