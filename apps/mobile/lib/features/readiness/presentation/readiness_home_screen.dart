import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../design/design.dart';
import '../application/readiness_controller.dart';
import '../domain/readiness_models.dart';
import 'widgets/readiness_entry_tile.dart';

/// Readiness Home — the hub for check-ins and their own record-keeping,
/// deliberately lighter than a dashboard: real trend *charts* for sleep/
/// HRV already live in Progress's own Recovery segment
/// (`docs/adr/0039-progress-module.md`), so this screen owns *records*
/// (today's status, check-in access, recent entries, one entry's full
/// detail) rather than re-charting the same data a second time. See
/// `docs/adr/0040-readiness-module.md` for the full reasoning behind
/// this split.
///
/// Like every other tab-root-adjacent screen in this app, this screen
/// holds no business logic — every branch renders directly off
/// [ReadinessHomeViewState]. Reached from Today's check-in nudge
/// (`ReadinessCheckInCard`) and from Progress's Recovery segment, not
/// from a bottom tab — Readiness has never been one of the five tabs
/// (UX/UI Design Bible Section 3).
class ReadinessHomeScreen extends ConsumerWidget {
  const ReadinessHomeScreen({super.key});

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
        title: const Text('Readiness'),
      ),
      body: state.when(
        loading: () => const _ReadinessHomeSkeleton(),
        error: (Object error, StackTrace stackTrace) => _ReadinessHomePageError(
          onRetry: () =>
              unawaited(ref.read(readinessHomeControllerProvider.notifier).refresh()),
        ),
        data: (ReadinessHomeViewState data) => _ReadinessHomeContent(
          state: data,
          onRefresh: () => ref.read(readinessHomeControllerProvider.notifier).refresh(),
        ),
      ),
    );
  }
}

class _ReadinessHomeSkeleton extends StatelessWidget {
  const _ReadinessHomeSkeleton();

  @override
  Widget build(BuildContext context) {
    return const SafeArea(
      child: Padding(
        padding: EdgeInsets.all(AppSpacing.lg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            AppSkeletonBox(width: double.infinity, height: 120),
            SizedBox(height: AppSpacing.xl),
            AppSkeletonBox(width: 140, height: 16),
            SizedBox(height: AppSpacing.md),
            AppSkeletonBox(width: double.infinity, height: 56),
            SizedBox(height: AppSpacing.sm),
            AppSkeletonBox(width: double.infinity, height: 56),
          ],
        ),
      ),
    );
  }
}

class _ReadinessHomePageError extends StatelessWidget {
  const _ReadinessHomePageError({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Center(
        child: AppErrorState(message: "Readiness couldn't be loaded.", onRetry: onRetry),
      ),
    );
  }
}

class _ReadinessHomeContent extends StatelessWidget {
  const _ReadinessHomeContent({required this.state, required this.onRefresh});

  final ReadinessHomeViewState state;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;

    if (!state.hasCheckedInEver) {
      return SafeArea(
        child: Center(
          child: AppEmptyState(
            icon: AppIcons.progress,
            title: 'Log your first check-in',
            message: 'Sleep, energy, stress, soreness, and recovery metrics '
                'take under a minute to record.',
            actionLabel: 'Start check-in',
            onAction: () => context.push('/readiness/check-in'),
          ),
        ),
      );
    }

    final List<ReadinessEntry> preview = state.entries.take(5).toList();

    return SafeArea(
      child: RefreshIndicator(
        onRefresh: onRefresh,
        color: colorScheme.primary,
        child: ListView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          children: <Widget>[
            if (state.isOffline) ...<Widget>[
              Text(
                'Offline — showing your last synced data',
                style: textTheme.labelMedium?.copyWith(color: colorScheme.onSurfaceVariant),
              ),
              const SizedBox(height: AppSpacing.lg),
            ],
            _TodayCheckInCard(state: state),
            const SizedBox(height: AppSpacing.xxl),
            AppSectionHeader(
              title: 'Recent check-ins',
              actionLabel: 'See all',
              onActionPressed: () => context.push('/readiness/timeline'),
            ),
            AppCard(
              padding: EdgeInsets.zero,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  for (final ReadinessEntry entry in preview)
                    ReadinessEntryTile(
                      entry: entry,
                      onTap: () => context.push('/readiness/entry/${entry.readinessId}'),
                    ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.xxl),
            AppListTile(
              leadingIcon: AppIcons.info,
              title: 'Recovery score',
              subtitle: 'How your check-ins turn into a readiness signal',
              trailing: Icon(AppIcons.chevronRight, color: colorScheme.onSurfaceVariant, size: 20),
              onTap: () => context.push('/readiness/formula'),
            ),
          ],
        ),
      ),
    );
  }
}

/// Today's own status card — the destination the Bible's own check-in
/// flow returns to ("Submit -> back to Today with the updated status
/// card," Section 6.5, reinterpreted here since Readiness has no tab of
/// its own for that status to live on permanently). Shows real recorded
/// values only, never a computed band or score — see this screen's own
/// class doc comment and `docs/adr/0040-readiness-module.md`.
class _TodayCheckInCard extends StatelessWidget {
  const _TodayCheckInCard({required this.state});

  final ReadinessHomeViewState state;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final ReadinessEntry? today = state.todayEntry;

    if (today == null) {
      return AppCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Text("Today's readiness check-in", style: textTheme.titleLarge),
            const SizedBox(height: AppSpacing.xs),
            Text(
              "You haven't checked in today yet.",
              style: textTheme.bodyMedium,
            ),
            const SizedBox(height: AppSpacing.lg),
            AppButton(
              label: 'Start check-in',
              onPressed: () => context.push('/readiness/check-in'),
            ),
          ],
        ),
      );
    }

    final List<(String, String)> rows = <(String, String)>[
      if (today.sleepDuration != null)
        ('Sleep', '${(today.sleepDuration!.inMinutes / 60).toStringAsFixed(1)}h'),
      if (today.sleepQuality != null) ('Sleep quality', '${today.sleepQuality}/10'),
      if (today.energyLevel != null) ('Energy', '${today.energyLevel}/10'),
      if (today.stressLevel != null) ('Stress', '${today.stressLevel}/10'),
      if (today.sorenessLevel != null) ('Soreness', '${today.sorenessLevel}/10'),
      if (today.restingHeartRate != null)
        ('Resting HR', '${today.restingHeartRate!.toStringAsFixed(0)} bpm'),
      if (today.heartRateVariability != null)
        ('HRV', '${today.heartRateVariability!.toStringAsFixed(0)} ms'),
    ];

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Row(
            children: <Widget>[
              Expanded(child: Text("Today's check-in", style: textTheme.titleLarge)),
              AppButton(
                label: 'Edit',
                variant: AppButtonVariant.tertiary,
                fullWidth: false,
                onPressed: () => context.push('/readiness/check-in'),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.md),
          for (final (String label, String value) in rows)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 2),
              child: Row(
                children: <Widget>[
                  Expanded(
                    child: Text(label, style: textTheme.bodyMedium?.copyWith(color: colorScheme.onSurfaceVariant)),
                  ),
                  Text(value, style: AppTypography.tabular(textTheme.bodyMedium ?? const TextStyle())),
                ],
              ),
            ),
          if (state.lastCheckInWarnings.isNotEmpty) ...<Widget>[
            const SizedBox(height: AppSpacing.lg),
            Text(
              'Advisory notes from your last check-in',
              style: textTheme.labelMedium?.copyWith(color: colorScheme.onSurfaceVariant),
            ),
            const SizedBox(height: AppSpacing.xs),
            for (final String warning in state.lastCheckInWarnings)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(warning, style: textTheme.bodySmall),
              ),
          ],
        ],
      ),
    );
  }
}
