import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../design/design.dart';
import '../../../shared/domain/coach_signal.dart';
import '../application/coach_controller.dart';
import '../domain/coach_models.dart';
import 'widgets/coach_signal_tile.dart';

/// Coach Home — the Coach tab's real content, replacing the old
/// placeholder `CoachScreen`. UX/UI Design Bible: Coach "surfaces
/// guidance derived from existing backend capabilities," not a chatbot.
/// This screen is a calm, filterable feed of real advisory signals —
/// severity, source module, and plain message text only, never a
/// fabricated score, confidence percentage, or predictive claim, and
/// never a chat composer. See `docs/adr/0041-coach-module.md` for the
/// full research this design is grounded in, including exactly why no
/// richer capability (a daily brief, a weekly rollup, a persisted
/// history) could be built honestly.
///
/// Like every other tab-root screen in this app, this screen holds no
/// business logic — every branch renders directly off
/// [CoachHomeViewState]; filtering by module is the one piece of
/// presentation-only logic here, and it is pure list filtering over
/// already-real data ([CoachHomeViewState.forModule]), never a second
/// data source.
class CoachHomeScreen extends ConsumerStatefulWidget {
  const CoachHomeScreen({super.key});

  @override
  ConsumerState<CoachHomeScreen> createState() => _CoachHomeScreenState();
}

class _CoachHomeScreenState extends ConsumerState<CoachHomeScreen> {
  CoachModule? _filter;

  @override
  Widget build(BuildContext context) {
    final AsyncValue<CoachHomeViewState> state = ref.watch(coachHomeControllerProvider);

    return state.when(
      loading: () => const _CoachHomeSkeleton(),
      error: (Object error, StackTrace stackTrace) => _CoachHomePageError(
        onRetry: () => unawaited(ref.read(coachHomeControllerProvider.notifier).refresh()),
      ),
      data: (CoachHomeViewState data) => _CoachHomeContent(
        state: data,
        filter: _filter,
        onFilterChanged: (CoachModule? module) => setState(() => _filter = module),
        onRefresh: () => ref.read(coachHomeControllerProvider.notifier).refresh(),
      ),
    );
  }
}

class _CoachHomeSkeleton extends StatelessWidget {
  const _CoachHomeSkeleton();

  @override
  Widget build(BuildContext context) {
    return const SafeArea(
      child: Padding(
        padding: EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.xxxl, AppSpacing.lg, AppSpacing.lg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            AppSkeletonBox(width: 100, height: 22),
            SizedBox(height: AppSpacing.xl),
            AppSkeletonBox(width: double.infinity, height: 72),
            SizedBox(height: AppSpacing.xl),
            AppSkeletonBox(width: double.infinity, height: 44, radius: AppRadius.radiusFull),
            SizedBox(height: AppSpacing.xl),
            AppSkeletonBox(width: double.infinity, height: 56),
            SizedBox(height: AppSpacing.sm),
            AppSkeletonBox(width: double.infinity, height: 56),
            SizedBox(height: AppSpacing.sm),
            AppSkeletonBox(width: double.infinity, height: 56),
          ],
        ),
      ),
    );
  }
}

class _CoachHomePageError extends StatelessWidget {
  const _CoachHomePageError({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Center(
        child: AppErrorState(message: "Coach couldn't be loaded.", onRetry: onRetry),
      ),
    );
  }
}

class _CoachHomeContent extends StatelessWidget {
  const _CoachHomeContent({
    required this.state,
    required this.filter,
    required this.onFilterChanged,
    required this.onRefresh,
  });

  final CoachHomeViewState state;
  final CoachModule? filter;
  final ValueChanged<CoachModule?> onFilterChanged;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final List<CoachSignal> filtered = state.forModule(filter);

    return SafeArea(
      child: RefreshIndicator(
        onRefresh: onRefresh,
        color: colorScheme.primary,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(
            AppSpacing.lg, AppSpacing.xxxl, AppSpacing.lg, AppSpacing.xxxl,
          ),
          children: <Widget>[
            Text('Coach', style: textTheme.titleLarge),
            if (state.isOffline) ...<Widget>[
              const SizedBox(height: AppSpacing.xs),
              Text(
                'Offline — showing your last synced data',
                style: textTheme.labelMedium?.copyWith(color: colorScheme.onSurfaceVariant),
              ),
            ],
            const SizedBox(height: AppSpacing.xl),
            const _HowCoachWorksCard(),
            const SizedBox(height: AppSpacing.xl),
            if (state.hasAnySignals) ...<Widget>[
              AppSegmentedControl<CoachModule?>(
                segments: const <(CoachModule?, String)>[
                  (null, 'All'),
                  (CoachModule.recovery, 'Recovery'),
                  (CoachModule.nutrition, 'Nutrition'),
                  (CoachModule.training, 'Training'),
                ],
                selected: filter,
                onChanged: onFilterChanged,
              ),
              const SizedBox(height: AppSpacing.xl),
            ],
            AppSectionHeader(
              title: 'Recent guidance',
              actionLabel: 'Weekly review',
              onActionPressed: () => context.push('/coach/weekly-review'),
            ),
            if (filtered.isEmpty)
              _CoachEmptyFeed(hasAnySignalsAtAll: state.hasAnySignals)
            else
              AppCard(
                padding: EdgeInsets.zero,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    for (final CoachSignal signal in filtered)
                      CoachSignalTile(
                        signal: signal,
                        onTap: () => context.push('/coach/signal/${signal.id}'),
                      ),
                  ],
                ),
              ),
            const SizedBox(height: AppSpacing.xxl),
            AppListTile(
              leadingIcon: AppIcons.info,
              title: 'Coaching history',
              subtitle: 'Look back at guidance from previous sessions',
              trailing: Icon(AppIcons.chevronRight, color: colorScheme.onSurfaceVariant, size: 20),
              onTap: () => context.push('/coach/history'),
            ),
          ],
        ),
      ),
    );
  }
}

/// The one place Coach explains itself — a permanent, quiet disclosure
/// card rather than a separate "About Coach" screen the Bible never
/// names, per this module's own consolidation discipline. States plainly
/// what Coach is (rule-based, real, sourced from actions already taken)
/// and is not (a chat assistant, a predictive model, a fabricated
/// score) — directly implementing this module's own design directive:
/// "Prioritize... explanations, reasoning, context," never "confidence"
/// (there is no confidence score anywhere in the backend to show).
class _HowCoachWorksCard extends StatelessWidget {
  const _HowCoachWorksCard();

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Row(
            children: <Widget>[
              Icon(AppIcons.info, size: 18, color: colorScheme.onSurfaceVariant),
              const SizedBox(width: AppSpacing.sm),
              Text('How this works', style: textTheme.titleMedium),
            ],
          ),
          const SizedBox(height: AppSpacing.xs),
          Text(
            'Every item below comes from a real, rule-based check that ran '
            'when you checked in, logged a meal, or completed a session — '
            'not a chat assistant and not a predicted score. Nothing here '
            "is generated unless you've taken an action for it to respond to.",
            style: textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }
}

class _CoachEmptyFeed extends StatelessWidget {
  const _CoachEmptyFeed({required this.hasAnySignalsAtAll});

  final bool hasAnySignalsAtAll;

  @override
  Widget build(BuildContext context) {
    if (!hasAnySignalsAtAll) {
      return const AppEmptyState(
        icon: AppIcons.coach,
        title: 'Nothing to show yet',
        message: 'Check in, log a meal, or complete a session and any real '
            'guidance from those actions will show up here.',
      );
    }
    return const AppEmptyState(
      icon: AppIcons.coach,
      title: 'Nothing in this category yet',
      message: 'No guidance from this area so far this session.',
    );
  }
}
