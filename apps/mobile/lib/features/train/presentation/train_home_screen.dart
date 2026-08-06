import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../design/design.dart';
import '../application/train_controller.dart';
import '../domain/train_models.dart';
import 'widgets/not_connected_placeholder.dart';
import 'widgets/train_history_tile.dart';
import 'widgets/train_workout_card.dart';

/// Train Home — the natural continuation of Today's own layout rhythm
/// (header, then content, no bespoke chrome): UX/UI Design Bible's
/// catalog entry, "Current plan overview, this week's sessions." The
/// three in-page tabs (Section 4: "This Week / History / Library") are
/// [AppSegmentedControl], this phase's own design-system extension — see
/// that component's doc comment for why it did not already exist and had
/// to be built rather than bypassed.
///
/// Like [TodayScreen], this screen holds no business logic — every
/// branch renders directly off [TrainHomeViewState].
class TrainHomeScreen extends ConsumerStatefulWidget {
  const TrainHomeScreen({super.key});

  @override
  ConsumerState<TrainHomeScreen> createState() => _TrainHomeScreenState();
}

enum _TrainTab { thisWeek, history, library }

class _TrainHomeScreenState extends ConsumerState<TrainHomeScreen> {
  _TrainTab _tab = _TrainTab.thisWeek;

  @override
  Widget build(BuildContext context) {
    final AsyncValue<TrainHomeViewState> state = ref.watch(trainHomeControllerProvider);

    return state.when(
      loading: () => const _TrainHomeSkeleton(),
      error: (Object error, StackTrace stackTrace) => _TrainHomePageError(
        onRetry: () =>
            unawaited(ref.read(trainHomeControllerProvider.notifier).refresh()),
      ),
      data: (TrainHomeViewState data) => _TrainHomeContent(
        state: data,
        tab: _tab,
        onTabChanged: (_TrainTab tab) => setState(() => _tab = tab),
        onRefresh: () => ref.read(trainHomeControllerProvider.notifier).refresh(),
      ),
    );
  }
}

class _TrainHomeSkeleton extends StatelessWidget {
  const _TrainHomeSkeleton();

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
            AppSkeletonBox(width: double.infinity, height: 44, radius: AppRadius.radiusFull),
            SizedBox(height: AppSpacing.xl),
            AppSkeletonBox(width: double.infinity, height: 96),
            SizedBox(height: AppSpacing.lg),
            AppSkeletonBox(width: double.infinity, height: 96),
          ],
        ),
      ),
    );
  }
}

class _TrainHomePageError extends StatelessWidget {
  const _TrainHomePageError({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Center(
        child: AppErrorState(message: "Train couldn't be loaded.", onRetry: onRetry),
      ),
    );
  }
}

class _TrainHomeContent extends StatelessWidget {
  const _TrainHomeContent({
    required this.state,
    required this.tab,
    required this.onTabChanged,
    required this.onRefresh,
  });

  final TrainHomeViewState state;
  final _TrainTab tab;
  final ValueChanged<_TrainTab> onTabChanged;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;

    if (!state.hasActivePlan) {
      return SafeArea(
        child: Center(
          child: AppEmptyState(
            icon: AppIcons.train,
            title: 'No training plan yet',
            message: 'Build a plan from Today to see your sessions here.',
          ),
        ),
      );
    }

    return SafeArea(
      child: RefreshIndicator(
        onRefresh: onRefresh,
        color: colorScheme.primary,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(
            AppSpacing.lg, AppSpacing.xxxl, AppSpacing.lg, AppSpacing.xxxl,
          ),
          children: <Widget>[
            Row(
              children: <Widget>[
                Expanded(child: Text('Train', style: textTheme.titleLarge)),
                AppButton(
                  label: 'Records',
                  variant: AppButtonVariant.tertiary,
                  fullWidth: false,
                  onPressed: () => context.push('/train/records'),
                ),
              ],
            ),
            if (state.isOffline) ...<Widget>[
              const SizedBox(height: AppSpacing.xs),
              Text(
                'Offline — showing your last synced data',
                style: textTheme.labelMedium?.copyWith(color: colorScheme.onSurfaceVariant),
              ),
            ],
            const SizedBox(height: AppSpacing.xl),
            AppSegmentedControl<_TrainTab>(
              segments: const <(_TrainTab, String)>[
                (_TrainTab.thisWeek, 'This Week'),
                (_TrainTab.history, 'History'),
                (_TrainTab.library, 'Library'),
              ],
              selected: tab,
              onChanged: onTabChanged,
            ),
            const SizedBox(height: AppSpacing.xl),
            switch (tab) {
              _TrainTab.thisWeek => _ThisWeekSection(workouts: state.thisWeek),
              _TrainTab.history => _HistorySection(sessions: state.history),
              _TrainTab.library => const NotConnectedPlaceholder(
                  title: 'Exercise library not connected yet',
                  message:
                      'Browsing and searching the exercise catalog needs a '
                      "backend endpoint that doesn't exist yet. This screen "
                      "is ready — it's wired up the moment that endpoint "
                      'ships.',
                ),
            },
          ],
        ),
      ),
    );
  }
}

class _ThisWeekSection extends StatelessWidget {
  const _ThisWeekSection({required this.workouts});

  final List<TrainWorkout> workouts;

  @override
  Widget build(BuildContext context) {
    if (workouts.isEmpty) {
      return const AppEmptyState(
        icon: AppIcons.train,
        title: 'Nothing planned this week',
        message: 'Check back once your next block is generated.',
      );
    }
    return Column(
      children: <Widget>[
        for (final TrainWorkout workout in workouts) ...<Widget>[
          TrainWorkoutCard(
            workout: workout,
            onTap: () => context.push('/train/pre-session/${workout.workoutId}'),
          ),
          const SizedBox(height: AppSpacing.md),
        ],
      ],
    );
  }
}

class _HistorySection extends StatelessWidget {
  const _HistorySection({required this.sessions});

  final List<TrainSession> sessions;

  @override
  Widget build(BuildContext context) {
    if (sessions.isEmpty) {
      return const AppEmptyState(
        icon: AppIcons.train,
        title: 'No completed sessions yet',
        message: 'Finished sessions will show up here.',
      );
    }
    return AppCard(
      padding: EdgeInsets.zero,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          for (final TrainSession session in sessions)
            TrainHistoryTile(
              session: session,
              onTap: () => context.push('/train/session/${session.sessionId}/summary'),
            ),
        ],
      ),
    );
  }
}
