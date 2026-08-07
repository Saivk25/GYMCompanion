import 'package:flutter/material.dart';

import '../../../../design/design.dart';
import '../../domain/progress_models.dart';

/// One metric's latest value in the Transformation dashboard's metric
/// list — reuses [AppListTile] (the same "one list-row component" rule
/// every other list in this app follows). Tapping opens that metric's
/// full trend detail.
class MeasurementListTile extends StatelessWidget {
  const MeasurementListTile({
    required this.metric,
    required this.value,
    required this.onTap,
    super.key,
  });

  final MeasurementMetric metric;
  final double value;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;

    return AppListTile(
      leadingIcon: AppIcons.progress,
      title: metric.label,
      subtitle: '${value.toStringAsFixed(1)} ${metric.unitSuffix}',
      trailing: Icon(AppIcons.chevronRight, color: colorScheme.onSurfaceVariant, size: 20),
      onTap: onTap,
    );
  }
}
