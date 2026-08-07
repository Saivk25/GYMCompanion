import 'package:flutter/material.dart';

import '../theme/app_semantic_colors.dart';
import '../tokens/tokens.dart';

/// Whether one day in an [AppWeekHeatmap] met its target. Deliberately
/// two values, not three: the UX/UI Design Bible (Section 12, "History /
/// adherence") is explicit that "missed days use a neutral absence
/// treatment, deliberately not red, to avoid guilt-color-coding" — a day
/// with nothing logged and a day that was logged but fell short read
/// identically here, both as the same neutral cell, because the Bible
/// draws no visual distinction between them either. Only [met] earns the
/// (muted, non-alarmist) success tone.
enum AppWeekHeatmapLevel { met, notMet }

/// A single week's seven-cell adherence row — the restrained,
/// GitHub-contribution-graph-style pattern Section 12 names, scoped down
/// to exactly one week (this app's only current use, Fuel's/Progress's
/// weekly nutrition pattern). Never a calendar-month grid: nothing in
/// this app currently needs one, and a 7-cell row is the honest shape
/// for "this week," not a smaller version of a larger chart this system
/// doesn't have a real need for yet — the same "don't build the bigger
/// shape before something needs it" discipline `AppColors.chart1-3`'s own
/// doc comment already applies to chart-series colors.
class AppWeekHeatmap extends StatelessWidget {
  const AppWeekHeatmap({
    required this.dayLabels,
    required this.levels,
    required this.semanticLabel,
    super.key,
  }) : assert(
          dayLabels.length == levels.length,
          'dayLabels and levels must be the same length',
        );

  /// One short label per day (e.g. `['M', 'T', 'W', 'T', 'F', 'S', 'S']`).
  final List<String> dayLabels;
  final List<AppWeekHeatmapLevel> levels;
  final String semanticLabel;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final AppSemanticColors semantic = Theme.of(context).semanticColors;
    final TextTheme textTheme = Theme.of(context).textTheme;

    return Semantics(
      label: semanticLabel,
      child: ExcludeSemantics(
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: <Widget>[
            for (int i = 0; i < dayLabels.length; i++)
              Column(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  DecoratedBox(
                    decoration: BoxDecoration(
                      color: levels[i] == AppWeekHeatmapLevel.met
                          ? semantic.successContainer
                          : colorScheme.surfaceContainerHighest,
                      borderRadius: AppRadius.radiusXs,
                    ),
                    child: const SizedBox(width: 28, height: 28),
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    dayLabels[i],
                    style: textTheme.labelSmall?.copyWith(
                      color: colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }
}
