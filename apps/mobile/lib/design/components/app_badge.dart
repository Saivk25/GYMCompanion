import 'package:flutter/material.dart';

import '../theme/app_semantic_colors.dart';
import '../tokens/tokens.dart';

/// A small status/metadata pill — the one badge/tag/chip-of-meaning
/// component this app uses for confidence tags, status labels, and
/// similar short, color-coded pieces of information (e.g. Meal Review's
/// per-item confidence tags, a "PR" marker, a readiness band label).
///
/// [AppBadge] always pairs its [tone] with both [icon] and [label] —
/// never color alone — directly implementing the accessibility rule
/// "color-independent communication" (this file's own doc comment is
/// the enforcement point: there is no constructor path that produces a
/// badge with color as the only signal, since [icon] and [label] are
/// both required, not optional). A user who cannot distinguish [tone]'s
/// color still reads the same information from the icon and text.
enum AppBadgeTone {
  /// Genuine achievement or a confirmed-good state (Bible: reserved for
  /// real milestones, not routine positive framing).
  success,

  /// Reduced-capacity or caution, never alarmist.
  warning,

  /// Reserved for Safety Escalation and destructive-action confirmation
  /// contexts — see `AppColors.danger`'s own doc comment.
  danger,

  /// Purely informational, no positive or negative valence — the
  /// default for most confidence tags and metadata.
  neutral,
}

class AppBadge extends StatelessWidget {
  const AppBadge({
    required this.label,
    required this.icon,
    this.tone = AppBadgeTone.neutral,
    super.key,
  });

  final String label;
  final IconData icon;
  final AppBadgeTone tone;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final AppSemanticColors semantic = Theme.of(context).semanticColors;
    final _BadgeColors colors = _resolveColors(tone, colorScheme, semantic);

    return DecoratedBox(
      decoration: BoxDecoration(
        color: colors.background,
        borderRadius: AppRadius.radiusFull,
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md,
          vertical: AppSpacing.xs,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Icon(icon, size: 14, color: colors.foreground),
            const SizedBox(width: AppSpacing.xs),
            // Flexible + ellipsis: a badge is `mainAxisSize.min` by
            // design (it should never claim more room than its content
            // needs), but the design system review's large-text audit
            // found that leaves it with no defense at all when a caller
            // places it somewhere width-constrained (a list tile's
            // trailing slot, a crowded metadata row) — at accessibility
            // text scales a long label could push the badge past its
            // available space instead of yielding to it. Flexible lets
            // the badge shrink to whatever room its parent actually
            // gives it; `ellipsis` is the correct failure mode for a
            // short status pill specifically (unlike a button's label,
            // truncating "High confidence" to "High conf…" still reads
            // as the same status, so wrapping to a second line — which
            // would break the pill's single-line shape — is the wrong
            // choice here).
            Flexible(
              child: Text(
                label,
                overflow: TextOverflow.ellipsis,
                style: AppTypography.labelMedium.copyWith(
                  color: colors.foreground,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  _BadgeColors _resolveColors(
    AppBadgeTone tone,
    ColorScheme colorScheme,
    AppSemanticColors semantic,
  ) {
    return switch (tone) {
      AppBadgeTone.success => _BadgeColors(
          background: semantic.successContainer,
          foreground: semantic.onSuccessContainer,
        ),
      AppBadgeTone.warning => _BadgeColors(
          background: semantic.warningContainer,
          foreground: semantic.onWarningContainer,
        ),
      AppBadgeTone.danger => _BadgeColors(
          background: colorScheme.errorContainer,
          foreground: colorScheme.onErrorContainer,
        ),
      AppBadgeTone.neutral => _BadgeColors(
          background: colorScheme.secondaryContainer,
          foreground: colorScheme.onSecondaryContainer,
        ),
    };
  }
}

class _BadgeColors {
  const _BadgeColors({required this.background, required this.foreground});

  final Color background;
  final Color foreground;
}
