import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../design/design.dart';
import '../application/progress_controller.dart';
import '../domain/progress_models.dart';
import '../domain/progress_series.dart';

/// One metric's full history — UX/UI Design Bible's "Measurement trend
/// detail" (Section 5.11 catalog: "One metric's full history. Return to
/// dashboard."). Reads from the same [progressHomeControllerProvider]
/// state Progress Home already holds rather than a second fetch: the
/// full measurement list Progress Home receives from
/// [ProgressRepository.fetchHome] already carries enough history to
/// drive this screen, so a second round trip for "more" history would
/// only duplicate data this app already has in memory.
class MeasurementTrendScreen extends ConsumerWidget {
  const MeasurementTrendScreen({required this.metric, super.key});

  final MeasurementMetric metric;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final AsyncValue<ProgressHomeViewState> state = ref.watch(progressHomeControllerProvider);

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(AppIcons.back),
          tooltip: 'Back',
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: Text(metric.label),
      ),
      body: state.when(
        loading: () => const Center(child: AppLoadingIndicator()),
        error: (Object error, StackTrace stackTrace) => Center(
          child: AppErrorState(
            message: "This trend couldn't be loaded.",
            onRetry: () => ref.read(progressHomeControllerProvider.notifier).refresh(),
          ),
        ),
        data: (ProgressHomeViewState data) => _TrendContent(metric: metric, data: data),
      ),
    );
  }
}

class _TrendContent extends StatelessWidget {
  const _TrendContent({required this.metric, required this.data});

  final MeasurementMetric metric;
  final ProgressHomeViewState data;

  @override
  Widget build(BuildContext context) {
    final List<ProgressEntry> oldestFirst = data.measurements.reversed.toList();
    final List<double?> raw = extractMetricSeries(oldestFirst, metric);

    if (raw.every((double? v) => v == null)) {
      return SafeArea(
        child: Center(
          child: AppEmptyState(
            icon: AppIcons.progress,
            title: 'No ${metric.label.toLowerCase()} logged yet',
            message: 'Log a check-in with this measurement to start a trend.',
          ),
        ),
      );
    }

    final List<double?> avg = rollingAverage(raw);
    final List<String> labels = <String>[for (final ProgressEntry e in oldestFirst) _shortDate(e.progressDate)];
    final double? latest = raw.lastWhere((double? v) => v != null, orElse: () => null);

    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(AppSpacing.lg),
        children: <Widget>[
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                Text(
                  latest != null ? '${latest.toStringAsFixed(1)} ${metric.unitSuffix}' : '—',
                  style: AppTypography.tabular(
                    Theme.of(context).textTheme.headlineMedium ?? const TextStyle(),
                  ),
                ),
                Text(
                  'Latest — rolling average shown below',
                  style: Theme.of(context)
                      .textTheme
                      .bodySmall
                      ?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant),
                ),
                const SizedBox(height: AppSpacing.lg),
                AppLineChart(
                  labels: labels,
                  values: avg,
                  rawValues: raw,
                  height: 220,
                  semanticLabel:
                      '${metric.label} rolling average trend, latest value '
                      '${latest?.toStringAsFixed(1) ?? "not recorded"} ${metric.unitSuffix}.',
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  static String _shortDate(DateTime date) => '${date.month}/${date.day}';
}
