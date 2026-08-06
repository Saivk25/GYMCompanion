import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../design/design.dart';
import '../application/today_controller.dart';
import '../domain/today_models.dart';
import 'widgets/readiness_checkin_card.dart';
import 'widgets/session_card.dart';
import 'widgets/today_task_card.dart';

/// The daily hub — UX/UI Design Bible Section 5.1: "The single daily
/// starting point — answers 'what should I do today' without requiring
/// navigation." Every element and every state below (empty/loading/
/// offline/error/success, and the interaction-priority ordering) traces
/// directly to that section's fourteen-field specification; see each
/// private widget's own doc comment for the specific line it implements.
///
/// This screen owns layout and sequencing only — it holds no business
/// logic itself. What to show is entirely decided by [TodayViewState]
/// (`../domain/today_models.dart`) and [TodayController]
/// (`../application/today_controller.dart`); every widget used here
/// (`AppCard`, `AppButton`, `AppEmptyState`, `AppErrorState`,
/// `AppSkeletonBox`, `AppBadge`) comes from the design system, per this
/// project's standing "everything from tokens/components, nothing
/// hardcoded" rule.
class TodayScreen extends ConsumerWidget {
  const TodayScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final AsyncValue<TodayViewState> state = ref.watch(todayControllerProvider);

    return state.when(
      loading: () => const _TodayPageSkeleton(),
      error: (Object error, StackTrace stackTrace) => _TodayPageError(
        // `onRetry` is a plain `VoidCallback` (AppErrorState's own type —
        // it has no concept of an async retry), but the controller's
        // `refresh()` returns a Future. `unawaited` makes discarding it
        // here an explicit, reviewed choice rather than the kind of
        // silently-dropped Future `unawaited_futures` (analysis_options.yaml)
        // exists to catch — the UI already reacts to the retry via
        // `ref.watch` picking up the new state, so nothing here needs to
        // wait on the Future itself.
        onRetry: () =>
            unawaited(ref.read(todayControllerProvider.notifier).refresh()),
      ),
      data: (TodayViewState data) => _TodayContent(
        state: data,
        onRefresh: () => ref.read(todayControllerProvider.notifier).refresh(),
      ),
    );
  }
}

/// Full-page skeleton for the *first* load only (UX/UI Design Bible's
/// loading state describes the session card specifically, but a genuine
/// first fetch has nothing else to show yet either — every element on
/// this page depends on the same initial call). Once real data has
/// loaded once, a subsequent per-card failure never falls back to this;
/// see [SessionCard]'s own skeleton for that narrower case.
class _TodayPageSkeleton extends StatelessWidget {
  const _TodayPageSkeleton();

  @override
  Widget build(BuildContext context) {
    return const SafeArea(
      child: Padding(
        padding: EdgeInsets.fromLTRB(
          AppSpacing.lg,
          AppSpacing.xxxl,
          AppSpacing.lg,
          AppSpacing.lg,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            AppSkeletonBox(width: 160, height: 16),
            SizedBox(height: AppSpacing.xxl),
            SessionCard(
              status: SessionCardStatus.loading,
              onStartSession: _noop,
              onTwoMinuteWin: _noop,
            ),
          ],
        ),
      ),
    );
  }
}

void _noop() {}

/// A genuine full-page fetch failure (no cached snapshot to fall back to
/// at all) — narrower than the session-card-scoped error the Bible
/// describes, and correctly rarer: this only fires when Today has never
/// successfully loaded, not on every plan-generation hiccup.
class _TodayPageError extends StatelessWidget {
  const _TodayPageError({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Center(
        child: AppErrorState(
          message: "Today couldn't be loaded.",
          onRetry: onRetry,
        ),
      ),
    );
  }
}

class _TodayContent extends StatelessWidget {
  const _TodayContent({required this.state, required this.onRefresh});

  final TodayViewState state;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;

    final List<Widget> children = <Widget>[
      _TodayHeader(state: state),
      const SizedBox(height: AppSpacing.xxl),
      // UX/UI Design Bible: "A not-yet-completed readiness check-in
      // outranks [the session card], appearing above [it] until
      // submitted."
      if (!state.checkInCompletedToday) ...<Widget>[
        ReadinessCheckInCard(
          onStart: () => _notBuiltYet(context, 'Readiness check-in'),
        ),
        const SizedBox(height: AppSpacing.xl),
      ],
      SessionCard(
        status: state.sessionStatus,
        session: state.session,
        onStartSession: () => _notBuiltYet(context, 'Active session'),
        onTwoMinuteWin: () => _notBuiltYet(context, 'Two-minute win'),
        onGetStarted: () => _notBuiltYet(context, 'Plan setup'),
        onBrowseLibrary: () => _notBuiltYet(context, 'Exercise library'),
      ),
      if (state.task != null) ...<Widget>[
        const SizedBox(height: AppSpacing.xl),
        TodayTaskCard(
          task: state.task!,
          onAction: () => _notBuiltYet(context, state.task!.actionLabel),
        ),
      ],
    ];

    return SafeArea(
      child: RefreshIndicator(
        onRefresh: onRefresh,
        color: colorScheme.primary,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(
            AppSpacing.lg,
            AppSpacing.xxxl,
            AppSpacing.lg,
            AppSpacing.xxxl,
          ),
          children: children,
        ),
      ),
    );
  }
}

/// The date, readiness band, offline indicator, and streak — one quiet
/// header block, not four competing elements. UX/UI Design Bible: the
/// band is always-displayed info; the streak is explicitly "understated"
/// (see its own reasoning below); offline gets only "a small offline
/// indicator," never a banner.
class _TodayHeader extends StatelessWidget {
  const _TodayHeader({required this.state});

  final TodayViewState state;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Row(
          children: <Widget>[
            Expanded(
              child: Text(_formattedDate(state.date), style: textTheme.titleLarge),
            ),
            // Only shown once today's check-in is done — while it's
            // outstanding, ReadinessCheckInCard itself is the signal;
            // showing the band chip too would say the same thing twice.
            if (state.checkInCompletedToday) _ReadinessBandChip(band: state.readinessBand),
          ],
        ),
        if (state.isOffline) ...<Widget>[
          const SizedBox(height: AppSpacing.xs),
          Text(
            'Offline — showing your last synced data',
            style: textTheme.labelMedium?.copyWith(color: colorScheme.onSurfaceVariant),
          ),
        ],
        if (state.streak != null) ...<Widget>[
          const SizedBox(height: AppSpacing.xs),
          _StreakLine(streak: state.streak!),
        ],
      ],
    );
  }

  static String _formattedDate(DateTime date) {
    const List<String> weekdays = <String>[
      'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
    ];
    const List<String> months = <String>[
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December',
    ];
    return '${weekdays[date.weekday - 1]}, ${months[date.month - 1]} ${date.day}';
  }
}

/// Readiness as a band chip (UX/UI Design Bible: "not a raw score by
/// default"). [AppBadgeTone.warning] covers both Light and Recovery —
/// distinguished by label text, not a fifth invented tone — per the
/// Bible's "no alarm-red overuse" and this design system's closed
/// four-tone badge vocabulary (see `AppBadge`'s own doc comment); Normal
/// uses [AppBadgeTone.neutral] rather than `.success`, since a routine
/// "nothing's wrong" day is not the genuine achievement `.success` is
/// reserved for. `.danger` is reserved for [ReadinessBand.escalate] —
/// the one band that is a real safety state, not a capacity note. The
/// icon changes with the tone too, not just the color — [AppBadge]'s
/// whole point is that meaning survives without color, so a color-blind
/// reading of "info circle" vs. "warning triangle" vs. "stop" must carry
/// the same distinction the tone does.
class _ReadinessBandChip extends StatelessWidget {
  const _ReadinessBandChip({required this.band});

  final ReadinessBand band;

  @override
  Widget build(BuildContext context) {
    final (String label, IconData icon, AppBadgeTone tone) = switch (band) {
      ReadinessBand.normal => ('Normal', AppIcons.info, AppBadgeTone.neutral),
      ReadinessBand.light => ('Light', AppIcons.warning, AppBadgeTone.warning),
      ReadinessBand.recovery => ('Recovery', AppIcons.warning, AppBadgeTone.warning),
      ReadinessBand.escalate => ('Conservative mode', AppIcons.danger, AppBadgeTone.danger),
    };
    return AppBadge(label: label, icon: icon, tone: tone);
  }
}

/// Quiet, text-only streak status — deliberately not a badge, not a
/// flame icon, not an accent color. The Domain Model Bible pairs a
/// streak's honesty guarantee with an explicit ban on shame-framed
/// messaging for a *broken* streak; the same restraint applied
/// symmetrically to an *active* one is why this renders as one small
/// caption line rather than a celebratory chip — a daily habit tracker
/// that visually cheers every single day stops meaning anything by the
/// second week, and reads as exactly the "gamification" this app's own
/// design philosophy rejects.
class _StreakLine extends StatelessWidget {
  const _StreakLine({required this.streak});

  final TodayStreak streak;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final String suffix = streak.graceUsed ? ' (grace used)' : '';

    return Text(
      '${streak.currentDays}-day streak$suffix',
      style: textTheme.labelMedium?.copyWith(color: colorScheme.onSurfaceVariant),
    );
  }
}

/// Every action this screen cannot yet complete — because the screen or
/// flow it leads to (Active Session, Readiness Check-in, Plan setup, the
/// Exercise Library) has not been built in this implementation order yet
/// — surfaces this, once, in one place, rather than failing silently.
/// Silent no-ops are indistinguishable from bugs; this is the same
/// disclosed-limitation posture ADR 0002 and `AppShell`'s own search/
/// notification icons already established, applied consistently here.
void _notBuiltYet(BuildContext context, String feature) {
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(content: Text('$feature is not built yet.')),
  );
}
