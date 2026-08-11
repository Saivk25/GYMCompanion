import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../design/design.dart';
import '../application/fuel_controller.dart';
import '../domain/fuel_models.dart';
import 'widgets/meal_entry_tile.dart';
import 'widgets/water_log_sheet.dart';

/// Fuel Home — UX/UI Design Bible Section 5.10: "The nutrition module's
/// daily hub — today's logged meals plus a glance at the week's
/// pattern." Every element and state below traces to that section's own
/// fourteen-field specification, the same discipline `TodayScreen`/
/// `TrainHomeScreen` already established for their own Bible sections.
///
/// This screen holds no business logic — every branch renders directly
/// off [FuelHomeViewState].
class FuelHomeScreen extends ConsumerWidget {
  const FuelHomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final AsyncValue<FuelHomeViewState> state = ref.watch(fuelHomeControllerProvider);

    return state.when(
      loading: () => const _FuelHomeSkeleton(),
      error: (Object error, StackTrace stackTrace) => _FuelHomePageError(
        onRetry: () =>
            unawaited(ref.read(fuelHomeControllerProvider.notifier).refresh()),
      ),
      data: (FuelHomeViewState data) => _FuelHomeContent(
        state: data,
        onRefresh: () => ref.read(fuelHomeControllerProvider.notifier).refresh(),
      ),
    );
  }
}

class _FuelHomeSkeleton extends StatelessWidget {
  const _FuelHomeSkeleton();

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
            AppSkeletonBox(width: double.infinity, height: 48),
            SizedBox(height: AppSpacing.xl),
            AppSkeletonBox(width: double.infinity, height: 88),
            SizedBox(height: AppSpacing.xl),
            AppSkeletonBox(width: 140, height: 16),
            SizedBox(height: AppSpacing.md),
            AppSkeletonBox(width: double.infinity, height: 64),
            SizedBox(height: AppSpacing.sm),
            AppSkeletonBox(width: double.infinity, height: 64),
          ],
        ),
      ),
    );
  }
}

class _FuelHomePageError extends StatelessWidget {
  const _FuelHomePageError({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Center(
        child: AppErrorState(message: "Fuel couldn't be loaded.", onRetry: onRetry),
      ),
    );
  }
}

/// A fixed default daily water target — 2000ml. No personalized
/// hydration goal exists anywhere in the domain model yet (there is no
/// such field on `User`/`UserPreferences`), so this is a disclosed,
/// reasonable constant rather than a fabricated per-user target. It only
/// shapes how full the progress bar reads; the real number
/// ([FuelHomeViewState.totalWaterMl]) is never hidden or rounded away.
const double _dailyWaterTargetMl = 2000;

class _FuelHomeContent extends StatelessWidget {
  const _FuelHomeContent({required this.state, required this.onRefresh});

  final FuelHomeViewState state;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final List<FuelEntry> meals = state.meals;

    return SafeArea(
      child: RefreshIndicator(
        onRefresh: onRefresh,
        color: colorScheme.primary,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(
            AppSpacing.lg, AppSpacing.xxxl, AppSpacing.lg, AppSpacing.xxxl,
          ),
          children: <Widget>[
            Text('Fuel', style: textTheme.titleLarge),
            if (state.isOffline) ...<Widget>[
              const SizedBox(height: AppSpacing.xs),
              Text(
                'Offline — meals log locally and sync automatically',
                style: textTheme.labelMedium?.copyWith(color: colorScheme.onSurfaceVariant),
              ),
            ],
            const SizedBox(height: AppSpacing.xl),
            AppButton(
              label: 'Log a meal',
              onPressed: () => context.push('/fuel/log-meal'),
            ),
            const SizedBox(height: AppSpacing.xl),
            _HydrationCard(totalMl: state.totalWaterMl),
            if (state.proteinConsistencyLabel != null) ...<Widget>[
              const SizedBox(height: AppSpacing.xl),
              _WeeklyPatternRow(label: state.proteinConsistencyLabel!),
            ],
            const SizedBox(height: AppSpacing.xl),
            AppListTile(
              leadingIcon: AppIcons.add,
              title: 'Supplements',
              subtitle: 'Dose tracking and schedule',
              trailing: Icon(AppIcons.chevronRight, color: colorScheme.onSurfaceVariant, size: 20),
              onTap: () => context.push('/fuel/supplements'),
            ),
            const SizedBox(height: AppSpacing.xxl),
            const AppSectionHeader(title: 'Today'),
            if (!state.hasLoggedAnyMealEver)
              const AppEmptyState(
                icon: AppIcons.fuel,
                title: 'Three ways to log a meal',
                message:
                    'Take a photo, describe it in text, or log a menu choice. '
                    "Whichever's fastest — nothing here is scored or judged.",
              )
            else if (meals.isEmpty)
              const AppEmptyState(
                icon: AppIcons.fuel,
                title: 'Nothing logged today yet',
              )
            else
              AppCard(
                padding: EdgeInsets.zero,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    for (final FuelEntry meal in meals) MealEntryTile(entry: meal),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}

/// Non-alarming hydration progress (Bible: "non-alarming hydration
/// progress") — a number and a flat bar, never a red/green pass-fail
/// treatment. "Log water" opens [WaterLogSheet], the same fast-entry
/// bottom-sheet pattern `QuickAddSheet` already established for Today.
class _HydrationCard extends StatelessWidget {
  const _HydrationCard({required this.totalMl});

  final double totalMl;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final double fraction = totalMl / _dailyWaterTargetMl;

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Row(
            children: <Widget>[
              Expanded(
                child: Text(
                  '${totalMl.round()} / ${_dailyWaterTargetMl.round()} ml',
                  style: textTheme.titleMedium,
                ),
              ),
              AppButton(
                label: 'Log water',
                variant: AppButtonVariant.tertiary,
                fullWidth: false,
                onPressed: () => showAppBottomSheet<void>(
                  context: context,
                  builder: (BuildContext context) => const WaterLogSheet(),
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.sm),
          AppProgressBar(fraction: fraction),
        ],
      ),
    );
  }
}

/// The weekly protein-consistency one-liner (Bible: "leads with pattern,
/// never a daily number, to avoid per-meal moralizing"). Tapping it
/// follows the Bible's own stated exit point — "Pattern tap -> Progress
/// > Nutrition dashboard" — real navigation to the Progress tab, which
/// is honest about being unbuilt itself rather than Fuel inventing a
/// dashboard of its own to fill the gap.
class _WeeklyPatternRow extends StatelessWidget {
  const _WeeklyPatternRow({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;

    return AppListTile(
      leadingIcon: AppIcons.progress,
      title: 'This week',
      subtitle: label,
      trailing: Icon(AppIcons.chevronRight, color: colorScheme.onSurfaceVariant, size: 20),
      onTap: () => context.go('/progress'),
    );
  }
}
