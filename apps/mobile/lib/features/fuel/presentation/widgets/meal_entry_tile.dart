import 'package:flutter/material.dart';

import '../../../../design/design.dart';
import '../../domain/fuel_models.dart';

/// One logged meal in Fuel Home's today list — reuses [AppListTile]
/// (the same "one list-row component" rule Today's task card and
/// Train's history tile already follow), never a bespoke card.
class MealEntryTile extends StatelessWidget {
  const MealEntryTile({required this.entry, super.key});

  final FuelEntry entry;

  @override
  Widget build(BuildContext context) {
    final String title = entry.mealType?.label ?? 'Meal';
    final List<String> macroParts = <String>[
      if (entry.calories != null) '${entry.calories!.round()} kcal',
      if (entry.protein != null) '${entry.protein!.round()}g protein',
    ];

    return AppListTile(
      leadingIcon: AppIcons.fuel,
      title: title,
      subtitle: <String>[
        _formattedTime(entry.recordedAt),
        if (macroParts.isNotEmpty) macroParts.join(' · '),
      ].join(' · '),
      trailing: entry.notes.isNotEmpty
          ? Icon(AppIcons.info, size: 16, color: Theme.of(context).colorScheme.onSurfaceVariant)
          : null,
    );
  }

  static String _formattedTime(DateTime time) {
    final int hour12 = time.hour % 12 == 0 ? 12 : time.hour % 12;
    final String minute = time.minute.toString().padLeft(2, '0');
    final String period = time.hour < 12 ? 'AM' : 'PM';
    return '$hour12:$minute $period';
  }
}
