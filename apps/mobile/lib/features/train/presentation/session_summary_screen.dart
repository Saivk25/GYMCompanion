import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../design/design.dart';
import '../application/train_controller.dart';
import '../domain/train_models.dart';
import 'widgets/session_progress_bar.dart';

/// Session Summary — reused for both the immediate post-session recap
/// (UX/UI Design Bible catalog: "Post-session recap... Return to Today")
/// and viewing a past completed session from History ("Session detail
/// (past)... Return to history"). One screen, not two near-identical
/// ones — the content the Bible specifies for each ("full detail of a
/// completed session" vs. "post-session recap") is the same information,
/// differing only in which exit action makes sense; see
/// `docs/adr/0037-train-module.md` for the full reasoning, and this
/// project's own directive: "If duplication appears, improve the
/// component library, not the screen."
///
/// [cameFromActiveSession] decides only the primary exit action's label
/// and destination — every other pixel on this screen is identical
/// either way.
class SessionSummaryScreen extends ConsumerWidget {
  const SessionSummaryScreen({
    required this.sessionId,
    required this.cameFromActiveSession,
    super.key,
  });

  final String sessionId;
  final bool cameFromActiveSession;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final AsyncValue<TrainSession> state = ref.watch(activeSessionControllerProvider(sessionId));

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(AppIcons.back),
          tooltip: 'Back',
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Session summary'),
      ),
      body: state.when(
        loading: () => const Center(child: AppLoadingIndicator()),
        error: (Object error, StackTrace stackTrace) => Center(
          child: AppErrorState(
            message: "This session couldn't be loaded.",
            onRetry: () => ref.invalidate(activeSessionControllerProvider(sessionId)),
          ),
        ),
        data: (TrainSession session) => _SummaryContent(
          session: session,
          cameFromActiveSession: cameFromActiveSession,
        ),
      ),
    );
  }
}

class _SummaryContent extends StatelessWidget {
  const _SummaryContent({required this.session, required this.cameFromActiveSession});

  final TrainSession session;
  final bool cameFromActiveSession;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final AppSemanticColors semantic = Theme.of(context).semanticColors;

    final (String statusLabel, AppBadgeTone statusTone) = switch (session.status) {
      SessionStatus.completed => ('Completed', AppBadgeTone.success),
      SessionStatus.abandoned => ('Ended early', AppBadgeTone.warning),
      SessionStatus.active => ('In progress', AppBadgeTone.neutral),
      SessionStatus.planned => ('Planned', AppBadgeTone.neutral),
    };
    final double completionFraction = (session.completionPercentage ?? 0) / 100;

    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(AppSpacing.lg),
        children: <Widget>[
          Row(
            children: <Widget>[
              Expanded(child: Text(session.workoutName, style: textTheme.headlineSmall)),
              AppBadge(
                label: statusLabel,
                icon: statusTone == AppBadgeTone.success ? AppIcons.success : AppIcons.info,
                tone: statusTone,
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.xs),
          Text(
            _formattedDate(session.sessionDate),
            style: textTheme.bodyMedium?.copyWith(color: colorScheme.onSurfaceVariant),
          ),
          const SizedBox(height: AppSpacing.xl),
          if (session.completionPercentage != null) ...<Widget>[
            Row(
              children: <Widget>[
                Text('Completion', style: textTheme.labelMedium),
                const Spacer(),
                Text(
                  '${session.completionPercentage!.round()}%',
                  style: textTheme.labelMedium,
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.xs),
            SessionProgressBar(fraction: completionFraction),
            const SizedBox(height: AppSpacing.lg),
          ],
          Row(
            children: <Widget>[
              if (session.durationSeconds != null) ...<Widget>[
                Icon(AppIcons.info, size: 16, color: colorScheme.onSurfaceVariant),
                const SizedBox(width: AppSpacing.xs),
                Text(
                  _formattedDuration(session.durationSeconds!),
                  style: textTheme.bodyMedium?.copyWith(color: colorScheme.onSurfaceVariant),
                ),
              ],
              if (session.rating != null) ...<Widget>[
                const SizedBox(width: AppSpacing.lg),
                Icon(AppIcons.successFilled, size: 16, color: semantic.success),
                const SizedBox(width: AppSpacing.xs),
                Text(
                  '${session.rating}/5',
                  style: textTheme.bodyMedium?.copyWith(color: colorScheme.onSurfaceVariant),
                ),
              ],
            ],
          ),
          const SizedBox(height: AppSpacing.xxl),
          Text('Exercises', style: textTheme.titleMedium),
          const SizedBox(height: AppSpacing.sm),
          if (session.exercisePerformances.isEmpty)
            const AppEmptyState(
              icon: AppIcons.train,
              title: 'No exercises logged',
              message: 'This session ended before anything was logged.',
            )
          else
            AppCard(
              padding: EdgeInsets.zero,
              elevation: AppElevationLevel.flat,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  for (final TrainExercisePerformance perf in session.exercisePerformances)
                    AppListTile(
                      title: perf.exerciseName,
                      subtitle: perf.sets.isEmpty
                          ? 'No sets logged'
                          : '${perf.sets.length} sets · '
                              '${perf.sets.map((s) => s.weight.toStringAsFixed(0)).toSet().join('/')}',
                      trailing: perf.isComplete
                          ? Icon(AppIcons.successFilled, color: semantic.success, size: 20)
                          : null,
                    ),
                ],
              ),
            ),
          const SizedBox(height: AppSpacing.xxxl),
          AppButton(
            label: cameFromActiveSession ? 'Return to Today' : 'Return to history',
            onPressed: () {
              if (cameFromActiveSession) {
                context.go('/today');
              } else {
                Navigator.of(context).pop();
              }
            },
          ),
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

  static String _formattedDuration(double seconds) {
    final int minutes = (seconds / 60).round();
    return '$minutes min';
  }
}
