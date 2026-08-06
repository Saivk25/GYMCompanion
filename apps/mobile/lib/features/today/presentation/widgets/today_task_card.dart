import 'package:flutter/material.dart';

import '../../../../design/design.dart';
import '../../domain/today_models.dart';

/// The single open Task or Recommendation awaiting a response (see
/// `TodayTask`'s own doc comment for why this is one card, never a
/// list). Ranks below the session card in the UX/UI Design Bible's
/// interaction priority — present, but not competing with the day's main
/// action.
class TodayTaskCard extends StatelessWidget {
  const TodayTaskCard({
    required this.task,
    required this.onAction,
    super.key,
  });

  final TodayTask task;
  final VoidCallback onAction;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;

    return AppCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(AppIcons.info, size: 20, color: colorScheme.onSurfaceVariant),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                Text(task.text, style: textTheme.bodyMedium),
                if (task.rationale != null) ...<Widget>[
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    task.rationale!,
                    style: textTheme.bodySmall?.copyWith(
                      color: colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
                const SizedBox(height: AppSpacing.sm),
                AppButton(
                  label: task.actionLabel,
                  onPressed: onAction,
                  variant: AppButtonVariant.tertiary,
                  fullWidth: false,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
