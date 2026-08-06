import 'package:flutter/widgets.dart';

import 'app_colors.dart';

/// The elevation system — exactly three tiers, per the UX/UI Design Bible
/// (Section 10: "A simple three-tier system — flat, raised card, overlay —
/// no arbitrary shadow variation").
///
/// Material's own default elevation scale offers six-plus discrete levels
/// (0, 1, 2, 3, 4, 6, 8, 12...). Left unconstrained, a codebase drifts into
/// using whichever of those a widget's default happens to be, so two
/// visually identical cards end up on different elevations for no reason
/// anyone chose. Naming exactly three meanings — content resting on the
/// canvas, a card raised off it, and a transient layer floating above
/// everything — and mapping every component to one of the three removes
/// that drift entirely: there is no fourth option to reach for.
///
/// ## Shadows are soft and low-opacity, not Material's default
///
/// Flutter's built-in `Material` elevation shadow (a single, fairly
/// opaque, tightly-blurred `BoxShadow`) reads as a generic Material demo
/// the moment you've seen it a few hundred times. The products this
/// system studies for craftsmanship (Linear, Notion, Stripe Dashboard)
/// use very low-opacity, large-blur, small-offset shadows — the shadow
/// suggests depth without drawing attention to itself. [shadowsFor]
/// implements that directly as [BoxShadow] lists for use on plain
/// [Container]/[DecoratedBox]-based components; [materialElevationFor]
/// gives the matching numeric `elevation` for genuine `Material`-family
/// widgets (`Card`, `AppBar`) where Flutter computes its own shadow from a
/// double.
///
/// ## Dark mode: tint, not shadow
///
/// A shadow is nearly invisible against a near-black background — the
/// physical metaphor (light casting a shadow) stops working once the
/// canvas itself is dark. The correct, well-established fix (the same one
/// Material 3's own dark theme guidance uses) is **surface tint**: a
/// raised surface in dark mode gets a slightly *lighter* fill than the
/// canvas behind it, so elevation reads through brightness, not shadow.
/// [shadowsFor] still returns a (very faint) shadow in dark mode for
/// subtlety at sharp edges, but the primary elevation signal in dark mode
/// comes from `AppColorScheme`'s surface-tint steps
/// (`lib/design/theme/app_color_scheme.dart`), not from this file.
enum AppElevationLevel {
  /// Content resting directly on the canvas — most of the app, most of
  /// the time. No shadow, no surface tint.
  flat,

  /// A card or row raised off the canvas — the default for any discrete
  /// content container. Subtle by design: a raised card should read as
  /// "a distinct group of content," not "an object floating in space."
  raised,

  /// A transient layer above the rest of the screen — a bottom sheet, a
  /// dialog, a popover menu. The only tier with a shadow strong enough to
  /// be consciously noticed, because it is the only tier whose entire job
  /// is to visually separate itself from everything behind it.
  overlay,
}

abstract final class AppElevation {
  /// `Material`-family `elevation` values matching [AppElevationLevel].
  static double materialElevationFor(AppElevationLevel level) {
    switch (level) {
      case AppElevationLevel.flat:
        return 0;
      case AppElevationLevel.raised:
        return 1;
      case AppElevationLevel.overlay:
        return 8;
    }
  }

  /// Soft, low-opacity shadow lists for plain [Container]/[DecoratedBox]
  /// components. [brightness] matters because a shadow tuned for a white
  /// canvas reads as a visible gray smudge on a dark one — the dark-mode
  /// shadows here are deliberately fainter, acting only as edge
  /// definition while [brightness]-aware surface tint (see the theme
  /// layer) carries the actual elevation signal.
  static List<BoxShadow> shadowsFor(
    AppElevationLevel level,
    Brightness brightness,
  ) {
    final bool isDark = brightness == Brightness.dark;
    switch (level) {
      case AppElevationLevel.flat:
        return const <BoxShadow>[];
      case AppElevationLevel.raised:
        return <BoxShadow>[
          BoxShadow(
            // ignore: deprecated_member_use
            color: (isDark ? AppColors.neutral1000 : AppColors.neutral900)
                .withOpacity(isDark ? 0.24 : 0.06),
            blurRadius: 12,
            offset: const Offset(0, 2),
          ),
        ];
      case AppElevationLevel.overlay:
        return <BoxShadow>[
          BoxShadow(
            // ignore: deprecated_member_use
            color: (isDark ? AppColors.neutral1000 : AppColors.neutral900)
                .withOpacity(isDark ? 0.4 : 0.12),
            blurRadius: 24,
            offset: const Offset(0, 8),
          ),
        ];
    }
  }
}
