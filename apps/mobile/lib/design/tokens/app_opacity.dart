import 'package:flutter/widgets.dart';

/// Interaction-state opacities — the token layer the pressed/hovered/
/// focused/disabled system in `AppTheme` and every interactive component
/// is built from, per the design system review's finding that these
/// states must be "token-driven... not default Material behavior."
///
/// ## Where these numbers come from
///
/// These are not invented. They are Material 3's own published state-layer
/// opacity values (hover 8%, focus/pressed 10%, dragged 16%) — reused for
/// the same reason `AppBreakpoints` reuses Material 3's window-size-class
/// boundaries rather than inventing new ones: an externally validated,
/// widely-implemented standard is a stronger foundation than a number
/// picked by eye, and reusing it means "why 8% and not 10%" already has a
/// documented answer outside this codebase. What *is* a decision made
/// here, not inherited, is disabling Material's default ripple
/// (`AppTheme`'s `splashFactory: NoSplash.splashFactory`) and using these
/// opacities to build a calmer, tint-only state layer in its place — see
/// [overlayFor].
///
/// [disabledContent] and [disabledContainer] follow Material's own
/// long-standing disabled-state convention: a disabled control is always
/// tinted from `ColorScheme.onSurface`, never from its own base color
/// (e.g. a disabled destructive button reads as gray, not as a faded
/// red) — the reasoning being that "disabled" is a single, universal
/// state that should look the same everywhere, independent of what it is
/// disabling.
abstract final class AppOpacity {
  static const double hovered = 0.08;
  static const double focused = 0.10;
  static const double pressed = 0.10;
  static const double selected = 0.12;
  static const double dragged = 0.16;

  /// The opacity of `onSurface` used for disabled *content* — text and
  /// icons on a disabled control.
  static const double disabledContent = 0.38;

  /// The opacity of `onSurface` used for a disabled control's own
  /// *container* fill (e.g. a disabled primary button's background).
  static const double disabledContainer = 0.12;

  /// Builds a [WidgetStateProperty] that tints [color] onto whatever it
  /// sits on top of, at the state-layer opacity for whichever interaction
  /// state is currently active — `null` (fully transparent, no tint) when
  /// idle. This is the single function every interactive component in
  /// this design system should use for its `overlayColor`, so "what does
  /// pressing this look like" is answered once, here, rather than
  /// redefined per component.
  ///
  /// Deliberately does not resolve [WidgetState.disabled] — a disabled
  /// control should show no interaction overlay at all (it cannot be
  /// pressed/hovered/focused), and its own *content*/*container* colors
  /// (see [disabledContent]/[disabledContainer]) already communicate the
  /// disabled state on their own.
  static WidgetStateProperty<Color?> overlayFor(Color color) {
    return WidgetStateProperty.resolveWith<Color?>((Set<WidgetState> states) {
      if (states.contains(WidgetState.pressed)) {
        // ignore: deprecated_member_use
        return color.withOpacity(pressed);
      }
      if (states.contains(WidgetState.hovered)) {
        // ignore: deprecated_member_use
        return color.withOpacity(hovered);
      }
      if (states.contains(WidgetState.focused)) {
        // ignore: deprecated_member_use
        return color.withOpacity(focused);
      }
      return null;
    });
  }
}
