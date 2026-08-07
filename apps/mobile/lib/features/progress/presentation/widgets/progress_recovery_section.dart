import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../design/design.dart';
import '../../../../shared/presentation/widgets/not_connected_placeholder.dart';
import '../../domain/progress_models.dart';

/// The Recovery dashboard segment — UX/UI Design Bible catalog:
/// "Readiness/recovery trend with visible formula." Only the *raw*
/// half of that spec is real: `ReadinessRuleEngine` (backend
/// `domain/readiness/rules/`) computes a composite score from five
/// inputs, but no endpoint returns that score or its per-rule
/// breakdown — `ReadinessResponse` exposes only the raw fields
/// themselves (see `docs/adr/0039-progress-module.md`). Charting the raw
/// sleep/HRV inputs that genuinely are real, and disclosing the
/// composite score as a distinct, honest gap rather than reimplementing
/// `ReadinessRuleEngine`'s formula in this client (which would risk
/// silently drifting from the real one, and puts business logic in a
/// widget either way), is the same "manual entry real, AI-shaped part
/// disclosed" split Fuel's own `LogMealScreen` already established.
/// (Energy/stress/soreness are bounded 1-10 self-report ratings, not
/// 1-5 — confirmed directly from `backend/app/domain/readiness/
/// value_objects.py` during the Readiness module's own research phase;
/// see `docs/adr/0040-readiness-module.md`. This doc comment previously
/// said 1-5, which was wrong.)
///
/// The "Readiness check-ins" row navigates to the real Readiness module
/// (`docs/adr/0040-readiness-module.md`) — real check-in submission,
/// timeline, and per-entry detail all live there now; this section
/// keeps owning the *trend charts* only, the same records-vs-trends
/// split that ADR documents, rather than duplicating check-in UI here.
class ProgressRecoverySection extends StatelessWidget {
  const ProgressRecoverySection({required this.week, super.key});

  final List<ReadinessDayEntry> week;

  @override
  Widget build(BuildContext context) {
    final bool hasHistory = week.any((ReadinessDayEntry d) => d.hasAnyEntry);

    if (!hasHistory) {
      return const AppEmptyState(
        icon: AppIcons.progress,
        title: 'Building your first trend',
        message: 'Log a readiness check-in from Today and your sleep and '
            'recovery trends will show up here.',
      );
    }

    final List<String> labels = <String>[for (final ReadinessDayEntry d in week) _weekdayInitial(d.date)];
    final List<double?> sleep = <double?>[for (final ReadinessDayEntry d in week) d.sleepHours];
    final List<double?> hrv = <double?>[for (final ReadinessDayEntry d in week) d.heartRateVariability];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              Text('Sleep, last 7 days', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: AppSpacing.lg),
              AppLineChart(
                labels: labels,
                values: sleep,
                semanticLabel: 'Sleep duration over the last 7 days, in hours.',
                height: 120,
              ),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.xl),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              Text('Heart rate variability, last 7 days', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: AppSpacing.lg),
              AppLineChart(
                labels: labels,
                values: hrv,
                semanticLabel: 'Heart rate variability over the last 7 days, in milliseconds.',
                height: 120,
              ),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.xl),
        AppListTile(
          leadingIcon: AppIcons.progress,
          title: 'Readiness check-ins',
          subtitle: 'Today\'s check-in, recovery timeline, and detail',
          trailing: Icon(AppIcons.chevronRight, color: Theme.of(context).colorScheme.onSurfaceVariant, size: 20),
          onTap: () => context.push('/readiness'),
        ),
        const SizedBox(height: AppSpacing.xl),
        const NotConnectedPlaceholder(
          title: 'Recovery score not connected yet',
          message:
              'A combined readiness score with its formula breakdown needs '
              "a backend endpoint that doesn't exist yet — the sleep and "
              'HRV trends above are your real logged data in the meantime.',
        ),
        const SizedBox(height: AppSpacing.xl),
        AppListTile(
          leadingIcon: AppIcons.progress,
          title: 'Correlations',
          subtitle: 'How readiness relates to training and nutrition',
          trailing: Icon(AppIcons.chevronRight, color: Theme.of(context).colorScheme.onSurfaceVariant, size: 20),
          onTap: () => context.push('/progress/insights'),
        ),
      ],
    );
  }

  static String _weekdayInitial(DateTime date) {
    const List<String> initials = <String>['M', 'T', 'W', 'T', 'F', 'S', 'S'];
    return initials[date.weekday - 1];
  }
}
