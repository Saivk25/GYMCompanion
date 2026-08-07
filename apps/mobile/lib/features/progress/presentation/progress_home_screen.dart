import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../design/design.dart';
import '../../../shared/presentation/widgets/not_connected_placeholder.dart';
import '../application/progress_controller.dart';
import '../domain/progress_models.dart';
import 'widgets/progress_nutrition_section.dart';
import 'widgets/progress_recovery_section.dart';
import 'widgets/progress_transformation_section.dart';

/// Progress Home — UX/UI Design Bible Section 3: "segmented sub-
/// navigation across Workout / Nutrition / Recovery / Transformation /
/// Reports dashboards, plus the photo and measurement timeline." The
/// five in-page tabs are [AppSegmentedControl] — Section 4 names
/// Progress's five dashboards explicitly as "the largest case the Bible
/// names" for that component, and that component's own doc comment
/// already anticipated this screen.
///
/// Two of the five segments (Nutrition, Transformation) render real data
/// from [ProgressRepository]; Recovery renders real raw readiness inputs
/// alongside one disclosed gap (the composite score); Workout and
/// Reports are total backend gaps and render [NotConnectedPlaceholder]
/// directly. See `docs/adr/0039-progress-module.md` for the full,
/// per-segment reasoning — none of this is guessed at inline here.
///
/// Like every other tab-root screen in this app, this screen holds no
/// business logic — every branch renders directly off
/// [ProgressHomeViewState].
class ProgressHomeScreen extends ConsumerStatefulWidget {
  const ProgressHomeScreen({super.key});

  @override
  ConsumerState<ProgressHomeScreen> createState() => _ProgressHomeScreenState();
}

enum _ProgressTab { workout, nutrition, recovery, transformation, reports }

class _ProgressHomeScreenState extends ConsumerState<ProgressHomeScreen> {
  _ProgressTab _tab = _ProgressTab.nutrition;

  @override
  Widget build(BuildContext context) {
    final AsyncValue<ProgressHomeViewState> state = ref.watch(progressHomeControllerProvider);

    return state.when(
      loading: () => const _ProgressHomeSkeleton(),
      error: (Object error, StackTrace stackTrace) => _ProgressHomePageError(
        onRetry: () =>
            unawaited(ref.read(progressHomeControllerProvider.notifier).refresh()),
      ),
      data: (ProgressHomeViewState data) => _ProgressHomeContent(
        state: data,
        tab: _tab,
        onTabChanged: (_ProgressTab tab) => setState(() => _tab = tab),
        onRefresh: () => ref.read(progressHomeControllerProvider.notifier).refresh(),
      ),
    );
  }
}

/// Bible Section 5.7's own loading rule for the Workout dashboard —
/// "skeleton chart shapes matching the final layout" — generalized here
/// to every segment, since all five share the same page-level fetch.
class _ProgressHomeSkeleton extends StatelessWidget {
  const _ProgressHomeSkeleton();

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
            AppSkeletonBox(width: 160, height: 18),
            SizedBox(height: AppSpacing.lg),
            AppSkeletonBox(width: double.infinity, height: 160),
            SizedBox(height: AppSpacing.xl),
            AppSkeletonBox(width: double.infinity, height: 96),
          ],
        ),
      ),
    );
  }
}

class _ProgressHomePageError extends StatelessWidget {
  const _ProgressHomePageError({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Center(
        child: AppErrorState(message: "Progress couldn't be loaded.", onRetry: onRetry),
      ),
    );
  }
}

class _ProgressHomeContent extends StatelessWidget {
  const _ProgressHomeContent({
    required this.state,
    required this.tab,
    required this.onTabChanged,
    required this.onRefresh,
  });

  final ProgressHomeViewState state;
  final _ProgressTab tab;
  final ValueChanged<_ProgressTab> onTabChanged;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;

    return SafeArea(
      child: RefreshIndicator(
        onRefresh: onRefresh,
        color: colorScheme.primary,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(
            AppSpacing.lg, AppSpacing.xxxl, AppSpacing.lg, AppSpacing.xxxl,
          ),
          children: <Widget>[
            Text('Progress', style: textTheme.titleLarge),
            if (state.isOffline) ...<Widget>[
              const SizedBox(height: AppSpacing.xs),
              Text(
                'Offline — showing your last synced data',
                style: textTheme.labelMedium?.copyWith(color: colorScheme.onSurfaceVariant),
              ),
            ],
            const SizedBox(height: AppSpacing.xl),
            AppSegmentedControl<_ProgressTab>(
              segments: const <(_ProgressTab, String)>[
                (_ProgressTab.workout, 'Workout'),
                (_ProgressTab.nutrition, 'Nutrition'),
                (_ProgressTab.recovery, 'Recovery'),
                (_ProgressTab.transformation, 'Transformation'),
                (_ProgressTab.reports, 'Reports'),
              ],
              selected: tab,
              onChanged: onTabChanged,
            ),
            const SizedBox(height: AppSpacing.xl),
            switch (tab) {
              _ProgressTab.workout => const NotConnectedPlaceholder(
                  title: 'Workout dashboard not connected yet',
                  message:
                      'Weekly volume, PR trends, and adherence need analytics '
                      "endpoints that don't exist yet — Train's own session "
                      'history is real today; this trend view is what reads '
                      "it back once it's built.",
                ),
              _ProgressTab.nutrition => ProgressNutritionSection(week: state.nutritionWeek),
              _ProgressTab.recovery => ProgressRecoverySection(week: state.readinessWeek),
              _ProgressTab.transformation => ProgressTransformationSection(
                  hasLoggedAnyMeasurementEver: state.hasLoggedAnyMeasurementEver,
                  measurementsNewestFirst: state.measurements,
                ),
              _ProgressTab.reports => const NotConnectedPlaceholder(
                  title: 'Reports not connected yet',
                  message:
                      'Generating and exporting a report needs a backend '
                      "endpoint that doesn't exist yet at all.",
                ),
            },
          ],
        ),
      ),
    );
  }
}
