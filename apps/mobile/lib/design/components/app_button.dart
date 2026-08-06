import 'package:flutter/material.dart';

import '../tokens/tokens.dart';

/// The one button component this app uses. Per the UX/UI Design Bible
/// (Section 10): "Strict hierarchy: exactly one primary button visible
/// per screen; secondary buttons are visually quieter; destructive
/// actions use a distinct, consistent treatment."
///
/// A screen reaching for a raw `ElevatedButton`/`OutlinedButton`/
/// `TextButton` instead of [AppButton] is exactly how button styling
/// drifts inconsistent screen by screen — [AppButton] exists so "which
/// button style do I use here" is answered by [AppButtonVariant], a
/// closed, reviewable choice, not by whichever raw Material widget a
/// screen's author reached for first. The four variants below are the
/// entire hierarchy this app has; there is no fifth.
enum AppButtonVariant {
  /// The single dominant action on a screen. Solid fill, highest
  /// contrast. A screen should very rarely show two of these at once —
  /// see the Bible rule above.
  primary,

  /// A visually quieter alternative action, present alongside a primary
  /// button without competing with it.
  secondary,

  /// The quietest tier — an action that must be available but should
  /// draw the least attention (e.g. "Skip", "Not now").
  tertiary,

  /// Irreversible or safety-relevant actions only (e.g. delete a
  /// session, confirm account deletion). A distinct, consistent
  /// treatment — never reused for an action that is merely important,
  /// per the Bible's own "undo over confirm" principle: something
  /// reversible does not need [destructive]'s visual weight.
  destructive,
}

class AppButton extends StatelessWidget {
  const AppButton({
    required this.label,
    required this.onPressed,
    this.variant = AppButtonVariant.primary,
    this.icon,
    this.isLoading = false,
    this.expand = true,
    super.key,
  });

  final String label;

  /// `null` renders the button in its disabled state — there is no
  /// separate `enabled` flag to keep in sync with this.
  final VoidCallback? onPressed;
  final AppButtonVariant variant;
  final IconData? icon;

  /// Replaces the label with an inline spinner and disables the button,
  /// without changing the button's size — a loading button must not
  /// cause the surrounding layout to jump.
  final bool isLoading;

  /// Whether the button fills the width available to it. `true` by
  /// default: most buttons in this app are the single full-width action
  /// at the bottom of a card or sheet. Set `false` for an inline button
  /// (e.g. a tertiary action next to a piece of text).
  final bool expand;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final VoidCallback? effectiveOnPressed = isLoading ? null : onPressed;

    final Widget content = isLoading
        ? SizedBox(
            height: 20,
            width: 20,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              valueColor: AlwaysStoppedAnimation<Color>(
                _foregroundColor(colorScheme),
              ),
            ),
          )
        : Row(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              if (icon != null) ...<Widget>[
                Icon(icon, size: 20),
                const SizedBox(width: AppSpacing.sm),
              ],
              Text(label),
            ],
          );

    final Widget button = switch (variant) {
      AppButtonVariant.primary => ElevatedButton(
          onPressed: effectiveOnPressed,
          child: content,
        ),
      AppButtonVariant.secondary => OutlinedButton(
          onPressed: effectiveOnPressed,
          child: content,
        ),
      AppButtonVariant.tertiary => TextButton(
          onPressed: effectiveOnPressed,
          child: content,
        ),
      AppButtonVariant.destructive => ElevatedButton(
          onPressed: effectiveOnPressed,
          style: ElevatedButton.styleFrom(
            backgroundColor: colorScheme.error,
            foregroundColor: colorScheme.onError,
          ),
          child: content,
        ),
    };

    if (!expand) {
      return button;
    }
    return SizedBox(width: double.infinity, child: button);
  }

  Color _foregroundColor(ColorScheme colorScheme) {
    return switch (variant) {
      AppButtonVariant.primary => colorScheme.onPrimary,
      AppButtonVariant.secondary => colorScheme.onSurface,
      AppButtonVariant.tertiary => colorScheme.primary,
      AppButtonVariant.destructive => colorScheme.onError,
    };
  }
}
