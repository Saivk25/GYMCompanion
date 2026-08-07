import 'package:flutter/material.dart';

import '../../../../design/design.dart';
import '../../domain/progress_models.dart';

/// The Nutrition dashboard segment — UX/UI Design Bible catalog:
/// "Macro/hydration/supplement trend view." Built from real per-day
/// totals ([ProgressHomeViewState.nutritionWeek], itself a client-side
/// sum of real logged `Nutrition` entries, the same legitimate
/// derivation `FuelHomeViewState.totalWaterMl` already performs for a
/// single day). Deliberately never a per-meal pie chart or score
/// (Section 12: "avoids per-meal moralizing") — a weekly protein trend
/// line plus a weekly consistency heatmap, exactly the two chart types
/// Section 12's own table names for nutrition.
class ProgressNutritionSection extends StatelessWidget {
  const ProgressNutritionSection({required this.week, super.key});

  final List<NutritionDayTotal> week;

  @override
  Widget build(BuildContext context) {
    final bool hasHistory = week.any((NutritionDayTotal d) => d.hasAnyEntry);

    if (!hasHistory) {
      // Bible Section 15's own phrase for this exact case: "'Building
      // your first trend' placeholder, never an empty chart frame."
      return const AppEmptyState(
        icon: AppIcons.progress,
        title: 'Building your first trend',
        message: 'Log a few days of meals in Fuel and your weekly protein '
            'pattern will show up here.',
      );
    }

    final List<String> labels = <String>[for (final NutritionDayTotal d in week) _weekdayInitial(d.date)];
    final List<double?> protein = <double?>[
      for (final NutritionDayTotal d in week) d.hasAnyEntry ? d.proteinGrams : null,
    ];
    final List<AppWeekHeatmapLevel> levels = <AppWeekHeatmapLevel>[
      for (final NutritionDayTotal d in week)
        d.metProteinTarget ? AppWeekHeatmapLevel.met : AppWeekHeatmapLevel.notMet,
    ];
    final int daysOnTarget = week.where((NutritionDayTotal d) => d.metProteinTarget).length;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              Text('Protein, last 7 days', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: AppSpacing.lg),
              AppLineChart(
                labels: labels,
                values: protein,
                referenceValue: kProteinTargetGrams,
                referenceLabel: 'Target',
                semanticLabel:
                    'Protein trend over the last 7 days, target ${kProteinTargetGrams.round()} grams. '
                    '$daysOnTarget of 7 days on target.',
              ),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.xl),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              Text('Weekly pattern', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: AppSpacing.lg),
              AppWeekHeatmap(
                dayLabels: labels,
                levels: levels,
                semanticLabel: '$daysOnTarget of the last 7 days met the protein target.',
              ),
            ],
          ),
        ),
      ],
    );
  }

  static String _weekdayInitial(DateTime date) {
    const List<String> initials = <String>['M', 'T', 'W', 'T', 'F', 'S', 'S'];
    return initials[date.weekday - 1];
  }
}
