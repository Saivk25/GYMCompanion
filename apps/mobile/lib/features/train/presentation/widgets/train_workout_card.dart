import 'package:flutter/material.dart';

import '../../../../design/design.dart';
import '../../domain/train_models.dart';

/// One planned workout, in Train Home's "This Week" list. An [AppCard]
/// (never a bespoke container) with a tappable [onTap] — tapping opens
/// the Pre-session screen for this workout, per the UX/UI Design Bible's
/// catalog entry for "Train home": "Open today's session or a past one."
class TrainWorkoutCard extends StatelessWidget {
  const TrainWorkoutCard({required this.workout, required this.onTap, super.key});

  final TrainWorkout workout;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;

    return AppCard(
      onTap: onTap,
      child: Row(
        children: <Widget>[
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                Text(workout.name, style: textTheme.titleMedium),
                const SizedBox(height: AppSpacing.xs),
                Text(
                  _formattedDate(workout.plannedDate),
                  style: textTheme.bodySmall?.copyWith(color: colorScheme.onSurfaceVariant),
                ),
                if (workout.goal != null) ...<Widget>[
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    workout.goal!,
                    style: textTheme.bodySmall,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          Icon(AppIcons.chevronRight, color: colorScheme.onSurfaceVariant, size: 20),
        ],
      ),
    );
  }

  static String _formattedDate(DateTime date) {
    final DateTime now = DateTime.now();
    final DateTime today = DateTime(now.year, now.month, now.day);
    final DateTime target = DateTime(date.year, date.month, date.day);
    final int diff = target.difference(today).inDays;
    if (diff == 0) return 'Today';
    if (diff == 1) return 'Tomorrow';
    const List<String> weekdays = <String>[
      'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun',
    ];
    return weekdays[date.weekday - 1];
  }
}
