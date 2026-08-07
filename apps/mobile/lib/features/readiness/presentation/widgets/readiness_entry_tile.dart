import 'package:flutter/material.dart';

import '../../../../design/design.dart';
import '../../domain/readiness_models.dart';

/// One logged check-in in Readiness Home's recent list or the full
/// Recovery Timeline — reuses [AppListTile] (the same "one list-row
/// component" rule every other list in this app follows).
class ReadinessEntryTile extends StatelessWidget {
  const ReadinessEntryTile({required this.entry, this.onTap, super.key});

  final ReadinessEntry entry;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final List<String> parts = <String>[
      if (entry.sleepDuration != null) '${_formatHours(entry.sleepDuration!)} sleep',
      if (entry.energyLevel != null) 'energy ${entry.energyLevel}/10',
      if (entry.stressLevel != null) 'stress ${entry.stressLevel}/10',
    ];

    return AppListTile(
      leadingIcon: AppIcons.progress,
      title: _formattedDate(entry.readinessDate),
      subtitle: parts.isEmpty ? 'No values recorded' : parts.join(' · '),
      trailing: onTap != null
          ? Icon(AppIcons.chevronRight, color: colorScheme.onSurfaceVariant, size: 20)
          : null,
      onTap: onTap,
    );
  }

  static String _formatHours(Duration d) {
    final double hours = d.inMinutes / 60;
    return '${hours.toStringAsFixed(1)}h';
  }

  static String _formattedDate(DateTime date) {
    const List<String> months = <String>[
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
    ];
    return '${months[date.month - 1]} ${date.day}';
  }
}
