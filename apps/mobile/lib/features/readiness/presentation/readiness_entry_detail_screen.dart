import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../design/design.dart';
import '../application/readiness_controller.dart';
import '../domain/readiness_models.dart';

/// Recovery Detail — one check-in's full recorded values. Reads from the
/// same [readinessHomeControllerProvider] state the timeline and home
/// screens already hold, the same "no second fetch for data already in
/// memory" reasoning `MeasurementTrendScreen` established for Progress.
class ReadinessEntryDetailScreen extends ConsumerWidget {
  const ReadinessEntryDetailScreen({required this.readinessId, super.key});

  final String readinessId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final AsyncValue<ReadinessHomeViewState> state = ref.watch(readinessHomeControllerProvider);

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(AppIcons.back),
          tooltip: 'Back',
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Check-in detail'),
      ),
      body: state.when(
        loading: () => const Center(child: AppLoadingIndicator()),
        error: (Object error, StackTrace stackTrace) => Center(
          child: AppErrorState(
            message: "This check-in couldn't be loaded.",
            onRetry: () => ref.read(readinessHomeControllerProvider.notifier).refresh(),
          ),
        ),
        data: (ReadinessHomeViewState data) {
          final Iterable<ReadinessEntry> matches =
              data.entries.where((ReadinessEntry e) => e.readinessId == readinessId);
          final ReadinessEntry? entry = matches.isEmpty ? null : matches.first;

          if (entry == null) {
            return const SafeArea(
              child: Center(
                child: AppEmptyState(
                  icon: AppIcons.progress,
                  title: 'Check-in not found',
                  message: 'It may have been part of an older session.',
                ),
              ),
            );
          }
          return _EntryDetail(entry: entry);
        },
      ),
    );
  }
}

class _EntryDetail extends StatelessWidget {
  const _EntryDetail({required this.entry});

  final ReadinessEntry entry;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;

    final List<(String, String)> rows = <(String, String)>[
      if (entry.sleepDuration != null)
        ('Sleep duration', '${(entry.sleepDuration!.inMinutes / 60).toStringAsFixed(1)}h'),
      if (entry.sleepQuality != null) ('Sleep quality', '${entry.sleepQuality}/10'),
      if (entry.energyLevel != null) ('Energy', '${entry.energyLevel}/10'),
      if (entry.stressLevel != null) ('Stress', '${entry.stressLevel}/10'),
      if (entry.sorenessLevel != null) ('Soreness', '${entry.sorenessLevel}/10'),
      if (entry.restingHeartRate != null)
        ('Resting heart rate', '${entry.restingHeartRate!.toStringAsFixed(0)} bpm'),
      if (entry.heartRateVariability != null)
        ('Heart rate variability', '${entry.heartRateVariability!.toStringAsFixed(0)} ms'),
    ];

    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(AppSpacing.lg),
        children: <Widget>[
          Text(_formattedDate(entry.readinessDate), style: textTheme.headlineSmall),
          const SizedBox(height: AppSpacing.xl),
          AppCard(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                if (rows.isEmpty)
                  Text('No values recorded.', style: textTheme.bodyMedium)
                else
                  for (final (String label, String value) in rows)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: Row(
                        children: <Widget>[
                          Expanded(
                            child: Text(
                              label,
                              style: textTheme.bodyMedium?.copyWith(color: colorScheme.onSurfaceVariant),
                            ),
                          ),
                          Text(value, style: AppTypography.tabular(textTheme.bodyMedium ?? const TextStyle())),
                        ],
                      ),
                    ),
              ],
            ),
          ),
          if (entry.notes.isNotEmpty) ...<Widget>[
            const SizedBox(height: AppSpacing.xl),
            Text('Notes', style: textTheme.titleMedium),
            const SizedBox(height: AppSpacing.sm),
            Text(entry.notes, style: textTheme.bodyMedium),
          ],
        ],
      ),
    );
  }

  static String _formattedDate(DateTime date) {
    const List<String> months = <String>[
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December',
    ];
    return '${months[date.month - 1]} ${date.day}, ${date.year}';
  }
}
