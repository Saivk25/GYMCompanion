import 'package:flutter/material.dart';

import '../../../../design/design.dart';
import '../../../../shared/domain/coach_signal.dart';

/// One real advisory signal in Coach Home's feed — reuses [AppListTile]
/// (the same "one list-row component" rule every list in this app
/// follows). Severity maps onto [AppBadgeTone] rather than inventing a
/// fifth color meaning: [CoachSeverity.critical] is the one genuine
/// safety-adjacent tier ([AppBadgeTone.danger]); [CoachSeverity.warning]
/// is reduced-capacity/caution ([AppBadgeTone.warning]); [CoachSeverity
/// .advisory] and [CoachSeverity.info] both read as calm, routine
/// information ([AppBadgeTone.neutral]) — advisory and info are kept
/// visually identical deliberately, since the Bible's own design
/// philosophy for Coach warns against alarming color "unless
/// communicating genuine problems," and a four-way color ramp for a
/// message list would read as more urgent than most of these messages
/// (mostly INFO/ADVISORY in practice) actually are.
class CoachSignalTile extends StatelessWidget {
  const CoachSignalTile({required this.signal, this.onTap, super.key});

  final CoachSignal signal;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;

    return AppListTile(
      leadingIcon: _iconFor(signal.module),
      title: signal.message,
      subtitle: '${signal.module.label} · ${_relativeTime(signal.occurredAt)}',
      trailing: onTap != null
          ? Icon(AppIcons.chevronRight, color: colorScheme.onSurfaceVariant, size: 20)
          : null,
      onTap: onTap,
    );
  }

  static IconData _iconFor(CoachModule module) => switch (module) {
        CoachModule.recovery => AppIcons.progress,
        CoachModule.nutrition => AppIcons.fuel,
        CoachModule.training => AppIcons.train,
      };

  static String _relativeTime(DateTime occurredAt) {
    final Duration elapsed = DateTime.now().difference(occurredAt);
    if (elapsed.inMinutes < 1) return 'just now';
    if (elapsed.inMinutes < 60) return '${elapsed.inMinutes}m ago';
    if (elapsed.inHours < 24) return '${elapsed.inHours}h ago';
    return '${elapsed.inDays}d ago';
  }
}

/// [AppBadge] for a [CoachSeverity] — see this file's own top comment
/// for the tone-mapping reasoning.
class CoachSeverityBadge extends StatelessWidget {
  const CoachSeverityBadge({required this.severity, super.key});

  final CoachSeverity severity;

  @override
  Widget build(BuildContext context) {
    final (IconData icon, AppBadgeTone tone) = switch (severity) {
      CoachSeverity.critical => (AppIcons.danger, AppBadgeTone.danger),
      CoachSeverity.warning => (AppIcons.warning, AppBadgeTone.warning),
      CoachSeverity.advisory => (AppIcons.info, AppBadgeTone.neutral),
      CoachSeverity.info => (AppIcons.info, AppBadgeTone.neutral),
    };
    return AppBadge(label: severity.label, icon: icon, tone: tone);
  }
}
