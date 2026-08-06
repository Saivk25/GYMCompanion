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
    this.fullWidth = true,
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
  /// (e.g. a tertiary action next to a piece of text). Named `fullWidth`,
  /// not `expand` — `expand` reads as "grow to fill", which is also a
  /// plausible (wrong) description of what a `Flexible`/`Expanded`
  /// wrapper does inside a `Row`/`Column`; `fullWidth` names the actual,
  /// unambiguous effect.
  final bool fullWidth;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final VoidCallback? effectiveOnPressed = isLoading ? null : onPressed;

    // Loading swaps the label for a spinner, but a screen reader must
    // still announce this control as "label, button" — not silently as
    // an unlabeled spinner. The design system review found the loading
    // branch dropping [Text] (and with it, the label an assistive
    // technology reads) entirely. [Semantics] here supplies [label]
    // explicitly and unconditionally — in both branches, not just the
    // loading one, so the announced label never depends on which
    // internal branch happened to render — and [excludeSemantics]
    // suppresses the spinner's own (unhelpful, "progress indicator")
    // semantics node from replacing it.
    final Widget content = Semantics(
      label: label,
      excludeSemantics: true,
      child: isLoading
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
                // Flexible, not a bare Text: the design system review's
                // large-text audit found this Row would overflow (not
                // wrap) at accessibility text scales once a label plus
                // icon no longer fits the button's available width — a
                // bare Text inside a Row has nothing forcing it to
                // respect the Row's remaining space. Flexible lets the
                // label wrap onto a second line inside the button
                // instead, which grows the button (its height is a
                // minimum, never a fixed cap) rather than clipping text
                // or overflowing past the button's edge.
                Flexible(
                  child: Text(label, softWrap: true),
                ),
              ],
            ),
    );

    // Two `switch (variant)` statements, not merged into one: this one
    // picks a *widget type* and runs after [content] already exists;
    // [_foregroundColor] resolves a *color* the spinner above needs
    // before [content] is built. They run at two different points in
    // this method for a real dependency-order reason, not by accident —
    // the design system review's "simplify duplicated switches" note was
    // evaluated and deliberately left as two, since merging them would
    // relocate this same logic rather than reduce it.
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

    if (!fullWidth) {
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
