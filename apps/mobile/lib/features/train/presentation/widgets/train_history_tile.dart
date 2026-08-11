import 'package:flutter/material.dart';

import '../../../../design/design.dart';
import '../../../../shared/presentation/app_date_format.dart';
import '../../domain/train_models.dart';

/// One past session, in Train Home's "History" list — reuses
/// [AppListTile] (the UX/UI Design Bible's own rule, Section 10: "a meal
/// row and a session-history row share the same underlying list-row
/// component"), never a bespoke row.
class TrainHistoryTile extends StatelessWidget {
  const TrainHistoryTile({required this.session, required this.onTap, super.key});

  final TrainSession session;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final (String label, IconData icon, AppBadgeTone tone) = switch (session.status) {
      SessionStatus.completed => ('Completed', AppIcons.success, AppBadgeTone.success),
      SessionStatus.abandoned => ('Ended early', AppIcons.warning, AppBadgeTone.warning),
      SessionStatus.active => ('In progress', AppIcons.info, AppBadgeTone.neutral),
      SessionStatus.planned => ('Planned', AppIcons.info, AppBadgeTone.neutral),
    };

    return AppListTile(
      leadingIcon: AppIcons.train,
      title: session.workoutName,
      subtitle: appShortMonthDay(session.sessionDate),
      trailing: AppBadge(label: label, icon: icon, tone: tone),
      onTap: onTap,
    );
  }
}
