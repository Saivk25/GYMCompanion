import 'package:flutter/material.dart';

import '../../../../design/design.dart';
import '../../domain/today_models.dart';

/// The single largest element on Today (UX/UI Design Bible Section 5.1:
/// "The session card is the single largest element") — except while
/// today's readiness check-in is still outstanding, in which case
/// `ReadinessCheckInCard` outranks it and renders above.
///
/// One widget, five renderings, switched on [status] — not five separate
/// widgets a parent has to choose between — because they are the same
/// card slot at different moments of the same day, never simultaneous,
/// and a screen reader / layout system should see one stable region here,
/// not a different widget type swapped in and out.
class SessionCard extends StatelessWidget {
  const SessionCard({
    required this.status,
    required this.onStartSession,
    required this.onTwoMinuteWin,
    this.session,
    this.onGetStarted,
    this.onBrowseLibrary,
    super.key,
  });

  final SessionCardStatus status;
  final TodaySessionSummary? session;

  final VoidCallback onStartSession;

  /// UX/UI Design Bible: "the two-minute-win option for tomorrow's
  /// context stays visible, never hidden" — offered alongside both
  /// [SessionCardStatus.ready] and [SessionCardStatus.completed], never
  /// only one of them.
  final VoidCallback onTwoMinuteWin;

  final VoidCallback? onGetStarted;
  final VoidCallback? onBrowseLibrary;

  @override
  Widget build(BuildContext context) {
    return switch (status) {
      SessionCardStatus.loading => const _SessionCardSkeleton(),
      SessionCardStatus.empty => AppEmptyState(
          icon: AppIcons.today,
          title: "Let's build your first plan",
          message:
              'Answer a few questions about your equipment and goals to '
              'get a plan built around them.',
          actionLabel: 'Get started',
          onAction: onGetStarted,
        ),
      SessionCardStatus.error => AppErrorState(
          message: "Today's session couldn't be built right now.",
          retryLabel: 'Browse exercise library',
          onRetry: onBrowseLibrary ?? () {},
        ),
      SessionCardStatus.ready => _SessionReadyCard(
          session: session,
          onStartSession: onStartSession,
          onTwoMinuteWin: onTwoMinuteWin,
        ),
      SessionCardStatus.completed => _SessionCompletedCard(
          session: session,
          onTwoMinuteWin: onTwoMinuteWin,
        ),
    };
  }
}

class _SessionReadyCard extends StatelessWidget {
  const _SessionReadyCard({
    required this.session,
    required this.onStartSession,
    required this.onTwoMinuteWin,
  });

  final TodaySessionSummary? session;
  final VoidCallback onStartSession;
  final VoidCallback onTwoMinuteWin;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final TodaySessionSummary? summary = session;

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Text("Today's session", style: textTheme.titleLarge),
          if (summary != null) ...<Widget>[
            const SizedBox(height: AppSpacing.xs),
            Text(summary.name, style: textTheme.titleMedium),
            if (summary.goal != null) ...<Widget>[
              const SizedBox(height: AppSpacing.xs),
              Text(
                summary.goal!,
                style: textTheme.labelMedium?.copyWith(
                  color: colorScheme.onSurfaceVariant,
                ),
              ),
            ],
            if (summary.notes != null) ...<Widget>[
              const SizedBox(height: AppSpacing.sm),
              Text(summary.notes!, style: textTheme.bodyMedium),
            ],
          ],
          const SizedBox(height: AppSpacing.lg),
          AppButton(label: 'Start session', onPressed: onStartSession),
          const SizedBox(height: AppSpacing.sm),
          Center(
            child: AppButton(
              label: 'Prefer a 2-minute version?',
              onPressed: onTwoMinuteWin,
              variant: AppButtonVariant.tertiary,
              fullWidth: false,
            ),
          ),
        ],
      ),
    );
  }
}

class _SessionCompletedCard extends StatelessWidget {
  const _SessionCompletedCard({
    required this.session,
    required this.onTwoMinuteWin,
  });

  final TodaySessionSummary? session;
  final VoidCallback onTwoMinuteWin;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final AppSemanticColors semantic = Theme.of(context).semanticColors;

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Row(
            children: <Widget>[
              Icon(AppIcons.successFilled, color: semantic.success, size: 22),
              const SizedBox(width: AppSpacing.sm),
              Text('Done for today', style: textTheme.titleLarge),
            ],
          ),
          if (session != null) ...<Widget>[
            const SizedBox(height: AppSpacing.sm),
            Text(
              session!.name,
              style: textTheme.bodyMedium?.copyWith(
                color: colorScheme.onSurfaceVariant,
              ),
            ),
          ],
          const SizedBox(height: AppSpacing.md),
          // Never hidden after completion (Bible, Section 5.1's Success
          // state) — tomorrow's fallback path stays reachable today too,
          // not gated behind "come back tomorrow first."
          AppButton(
            label: 'Log a 2-minute win for tomorrow',
            onPressed: onTwoMinuteWin,
            variant: AppButtonVariant.tertiary,
            fullWidth: false,
          ),
        ],
      ),
    );
  }
}

/// A skeleton matching [_SessionReadyCard]'s approximate shape — never a
/// spinner (UX/UI Design Bible, Section 5.1's Loading state).
class _SessionCardSkeleton extends StatelessWidget {
  const _SessionCardSkeleton();

  @override
  Widget build(BuildContext context) {
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          const AppSkeletonBox(width: 140, height: 22),
          const SizedBox(height: AppSpacing.sm),
          const AppSkeletonBox(width: 100, height: 14),
          const SizedBox(height: AppSpacing.sm),
          const AppSkeletonBox(width: 220, height: 16),
          const SizedBox(height: AppSpacing.lg),
          const AppSkeletonBox(width: double.infinity, height: 48),
        ],
      ),
    );
  }
}
