import 'package:flutter/material.dart';

import '../tokens/tokens.dart';

/// A consistent heading + optional trailing action row, used to
/// introduce a section within a screen (e.g. "This Week" above a list,
/// "Recent Activity" above a history preview). Repeating this exact
/// layout by hand on every screen is how heading style and spacing
/// silently drift between screens; [AppSectionHeader] is the one place
/// that layout is decided.
class AppSectionHeader extends StatelessWidget {
  const AppSectionHeader({
    required this.title,
    this.actionLabel,
    this.onActionPressed,
    super.key,
  });

  final String title;

  /// A short trailing text action (e.g. "See all"). `null` renders no
  /// trailing action at all — most section headers have none.
  final String? actionLabel;
  final VoidCallback? onActionPressed;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final TextTheme textTheme = Theme.of(context).textTheme;

    return Padding(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.lg,
        vertical: AppSpacing.sm,
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: <Widget>[
          // Expanded, not a bare Text with `mainAxisAlignment:
          // spaceBetween` — the design system review's large-text audit
          // found a long title at accessibility text scales, alongside a
          // trailing action, would overflow the Row rather than wrap
          // (a bare Text has no width limit forcing it to). Expanded
          // gives the title the remaining space after the trailing
          // button claims its own — title wraps onto a second line
          // instead of overflowing — and already pushes the trailing
          // button to the far edge, so the explicit `spaceBetween` this
          // replaced is no longer needed.
          Expanded(
            child: Text(title, style: textTheme.titleLarge),
          ),
          // Deliberately does *not* set `minimumSize`/`tapTargetSize` —
          // the design system review found this button shrinking its own
          // tap target to `Size.zero` with `shrinkWrap`, undercutting the
          // 48dp minimum the app-wide `textButtonTheme` (`AppTheme`)
          // already establishes for every other `TextButton` in the app.
          // Only `padding` and `foregroundColor` are overridden here, for
          // this button's intentionally compact visual footprint; the
          // 48dp minimum bound is inherited from the theme rather than
          // re-decided locally. A borderless, fill-less `TextButton`
          // growing its invisible layout bounds changes nothing anyone
          // can see — only what they can reliably tap.
          if (actionLabel != null)
            TextButton(
              onPressed: onActionPressed,
              style: TextButton.styleFrom(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.sm,
                  vertical: AppSpacing.xs,
                ),
                foregroundColor: colorScheme.primary,
              ),
              child: Text(actionLabel!),
            ),
        ],
      ),
    );
  }
}
