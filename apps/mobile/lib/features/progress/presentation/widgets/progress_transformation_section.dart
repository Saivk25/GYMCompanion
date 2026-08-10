import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../design/design.dart';
import '../../domain/progress_models.dart';
import '../../domain/progress_series.dart';
import 'measurement_list_tile.dart';

/// The Transformation dashboard segment — UX/UI Design Bible catalog:
/// "Photo comparison and measurement trends." Measurements are real
/// (`Progress`'s own append-only-by-policy record, backend-confirmed);
/// photos are not — no photo field, model, or route exists anywhere in
/// the backend (`docs/adr/0039-progress-module.md`) — so this section is
/// a real measurement dashboard with two honest, reachable placeholders
/// for the photo half of the Bible's own name for it, never a silent
/// omission.
///
/// Also renders [lastLogWarnings] — real `ProgressEvaluationRuleEngine`
/// advisory strings from the most recent log — inline below the latest
/// summary card, mirroring `ReadinessHomeScreen`'s own "Advisory notes
/// from your last check-in" pattern.
class ProgressTransformationSection extends StatelessWidget {
  const ProgressTransformationSection({
    required this.hasLoggedAnyMeasurementEver,
    required this.measurementsNewestFirst,
    this.lastLogWarnings = const <String>[],
    super.key,
  });

  final bool hasLoggedAnyMeasurementEver;
  final List<ProgressEntry> measurementsNewestFirst;

  /// Real `ProgressEvaluationRuleEngine` advisory strings from the most
  /// recent [ProgressRepository.logMeasurement] call, rendered inline
  /// rather than pushed to `CoachSignalLog` — see [ProgressLogResult]'s
  /// own doc comment (`progress_models.dart`) for why.
  final List<String> lastLogWarnings;

  @override
  Widget build(BuildContext context) {
    if (!hasLoggedAnyMeasurementEver) {
      // Bible Section 15's own phrase for this exact case: "Prompts the
      // first baseline capture."
      return AppEmptyState(
        icon: AppIcons.progress,
        title: 'Log your first check-in',
        message: 'Weight and measurements build a real trend the moment '
            'you log your first one.',
        actionLabel: 'Log measurements',
        onAction: () => context.push('/progress/log-measurement'),
      );
    }

    final List<ProgressEntry> oldestFirst = measurementsNewestFirst.reversed.toList();
    final List<String> labels = <String>[for (final ProgressEntry e in oldestFirst) _shortDate(e.progressDate)];
    final List<double?> weightRaw = extractMetricSeries(oldestFirst, MeasurementMetric.weight);
    final List<double?> weightAvg = rollingAverage(weightRaw);

    final ProgressEntry latest = measurementsNewestFirst.first;
    final ProgressEntry? previous =
        measurementsNewestFirst.length > 1 ? measurementsNewestFirst[1] : null;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        _LatestSummaryCard(latest: latest, previous: previous),
        if (lastLogWarnings.isNotEmpty) ...<Widget>[
          const SizedBox(height: AppSpacing.lg),
          Text(
            'Advisory notes from your last check-in',
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
          const SizedBox(height: AppSpacing.xs),
          for (final String warning in lastLogWarnings)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(warning, style: Theme.of(context).textTheme.bodySmall),
            ),
        ],
        const SizedBox(height: AppSpacing.xl),
        AppButton(
          label: 'Log measurements',
          onPressed: () => context.push('/progress/log-measurement'),
        ),
        if (weightRaw.any((double? v) => v != null)) ...<Widget>[
          const SizedBox(height: AppSpacing.xl),
          AppCard(
            onTap: () => context.push('/progress/measurement/${MeasurementMetric.weight.name}'),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                Text('Weight, rolling average', style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: AppSpacing.lg),
                AppLineChart(
                  labels: labels,
                  values: weightAvg,
                  rawValues: weightRaw,
                  semanticLabel:
                      'Weight rolling average trend, latest value '
                      '${latest.bodyWeight?.toStringAsFixed(1) ?? "not recorded"} kilograms.',
                ),
              ],
            ),
          ),
        ],
        const SizedBox(height: AppSpacing.xl),
        AppCard(
          padding: EdgeInsets.zero,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              for (final MeasurementMetric metric in _otherLoggedMetrics(latest))
                MeasurementListTile(
                  metric: metric,
                  value: metric.valueFrom(latest)!,
                  onTap: () => context.push('/progress/measurement/${metric.name}'),
                ),
              AppListTile(
                leadingIcon: AppIcons.camera,
                title: 'New photo check-in',
                subtitle: 'Standardized, protocol-guided capture',
                trailing: Icon(AppIcons.chevronRight, color: Theme.of(context).colorScheme.onSurfaceVariant, size: 20),
                onTap: () => context.push('/progress/photo-checkin'),
              ),
              AppListTile(
                leadingIcon: AppIcons.compare,
                title: 'Compare photos',
                subtitle: 'Side-by-side, synced-pose comparison',
                trailing: Icon(AppIcons.chevronRight, color: Theme.of(context).colorScheme.onSurfaceVariant, size: 20),
                onTap: () => context.push('/progress/photo-comparison'),
              ),
            ],
          ),
        ),
      ],
    );
  }

  static List<MeasurementMetric> _otherLoggedMetrics(ProgressEntry latest) {
    return <MeasurementMetric>[
      for (final MeasurementMetric metric in MeasurementMetric.values)
        if (metric != MeasurementMetric.weight && metric.valueFrom(latest) != null) metric,
    ];
  }

  static String _shortDate(DateTime date) => '${date.month}/${date.day}';
}

/// The latest logged weight, plus a plain, non-alarming delta against
/// the previous entry — no red/green pass-fail treatment (Bible Section
/// 11: "explicitly rejects red/green pass-fail framing on body
/// metrics"), just a neutral direction and number.
class _LatestSummaryCard extends StatelessWidget {
  const _LatestSummaryCard({required this.latest, required this.previous});

  final ProgressEntry latest;
  final ProgressEntry? previous;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final double? weight = latest.bodyWeight;
    final double? previousWeight = previous?.bodyWeight;
    final double? delta = (weight != null && previousWeight != null) ? weight - previousWeight : null;

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Text('Latest weight', style: textTheme.labelMedium?.copyWith(color: colorScheme.onSurfaceVariant)),
          const SizedBox(height: AppSpacing.xs),
          Text(
            weight != null ? '${weight.toStringAsFixed(1)} kg' : 'Not recorded',
            style: AppTypography.tabular(textTheme.headlineMedium ?? const TextStyle()),
          ),
          if (delta != null) ...<Widget>[
            const SizedBox(height: AppSpacing.xs),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                Icon(
                  delta == 0
                      ? AppIcons.trendFlat
                      : (delta < 0 ? AppIcons.trendDown : AppIcons.trendUp),
                  size: 14,
                  color: colorScheme.onSurfaceVariant,
                ),
                const SizedBox(width: AppSpacing.xs),
                Text(
                  '${delta.abs().toStringAsFixed(1)} kg vs last check-in',
                  style: textTheme.bodySmall?.copyWith(color: colorScheme.onSurfaceVariant),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
