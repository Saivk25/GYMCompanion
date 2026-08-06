import 'package:flutter/material.dart';

import '../theme/app_color_scheme.dart';
import '../tokens/tokens.dart';

/// The one card container this app uses. Per the UX/UI Design Bible
/// (Section 10): "The primary content container everywhere; one visual
/// card style, varied only by content, never by ad hoc per-screen
/// styling."
///
/// Structured as an outer, unclipped [DecoratedBox] carrying only the
/// shadow, wrapping an inner [Material] that carries the fill color,
/// corner radius, and (when tappable) ink feedback — deliberately not
/// Flutter's [Card] widget. [Card]'s default shadow model is tied to a
/// numeric `elevation` the framework renders itself, which produces the
/// somewhat heavy, immediately-recognizable "Material demo" shadow this
/// system works to avoid (see `AppElevation`'s doc comment for the full
/// reasoning on soft, low-opacity shadows instead). The two-layer split
/// matters: a shadow must be free to paint *outside* the card's bounds,
/// while the ink/content layer must be *clipped* to the card's rounded
/// corners — one [Material] alone cannot do both at once without either
/// clipping its own shadow off or letting ink effects bleed past the
/// rounded corners.
///
/// [AppCard] resolves its own fill from [AppColorScheme.surfaceAt], so it
/// automatically renders correctly in both themes, including dark mode's
/// tint-based elevation.
///
/// [onTap] is optional: a purely informational card (most of them) is
/// `null` and renders with no interactive affordance; a tappable card
/// (e.g. a list-style summary that opens a detail screen) supplies
/// [onTap] and gets the correct hover/focus/pressed behavior without a
/// caller needing to wrap it in its own [InkWell].
class AppCard extends StatelessWidget {
  const AppCard({
    required this.child,
    this.onTap,
    this.padding = const EdgeInsets.all(AppSpacing.lg),
    this.elevation = AppElevationLevel.raised,
    super.key,
  });

  final Widget child;
  final VoidCallback? onTap;
  final EdgeInsetsGeometry padding;

  /// [AppElevationLevel.flat] is a legitimate choice here too — a card
  /// nested inside another card, or one sitting in a context where a
  /// shadow would be visually redundant, should still get [AppCard]'s
  /// fill, radius, and padding without a second shadow stacking on top
  /// of its parent's. A flat card renders a hairline border instead, so
  /// it remains visually distinct from its surroundings without a
  /// shadow.
  final AppElevationLevel elevation;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final Color fill = AppColorScheme.surfaceAt(colorScheme, elevation);
    final List<BoxShadow> shadows = AppElevation.shadowsFor(
      elevation,
      colorScheme.brightness,
    );

    final Widget paddedChild = Padding(padding: padding, child: child);

    final Widget surface = Material(
      color: fill,
      borderRadius: AppRadius.radiusMd,
      clipBehavior: Clip.antiAlias,
      child: onTap == null
          ? paddedChild
          : InkWell(onTap: onTap, child: paddedChild),
    );

    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: AppRadius.radiusMd,
        boxShadow: shadows,
        border: elevation == AppElevationLevel.flat
            ? Border.all(color: colorScheme.outlineVariant)
            : null,
      ),
      child: surface,
    );
  }
}
