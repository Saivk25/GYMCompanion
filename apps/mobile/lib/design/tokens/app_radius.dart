import 'package:flutter/widgets.dart';

/// The corner-radius scale — restrained on purpose.
///
/// ## Why small radii read as premium and large radii read as generic
///
/// Oversized rounded corners (20-32px "bubble" cards) are one of the
/// fastest tells of an unstyled or AI-generated Flutter screen — it is
/// the single easiest visual flourish to reach for with zero design
/// judgment, so it is exactly the flourish that has become associated
/// with template output rather than considered design. The products this
/// system studies for craftsmanship (Linear, Stripe Dashboard, Things 3)
/// use tight-to-moderate radii — 4 to 12px — on structural containers,
/// and reserve fully rounded ("pill") shapes for small, discrete controls
/// where the shape itself carries meaning (a toggle, a chip, an avatar).
/// A card is not a pill; giving it pill-adjacent corners has no
/// functional justification, which is the "if it exists only because it
/// looks cool, remove it" rule applied to geometry instead of color.
///
/// [none] and [full] are the two extremes and are not part of the
/// numeric progression: [none] is for elements that must align flush
/// against an edge or another element (a table cell, a full-bleed image),
/// and [full] (a very large fixed value, not a proportion) is reserved
/// for genuinely circular/pill shapes — an avatar, a filter chip, a
/// toggle track — never for anything a user would describe as "a card"
/// or "a container."
abstract final class AppRadius {
  static const double none = 0;
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 12;
  static const double lg = 16;

  /// Large enough to fully round any control this app actually builds
  /// (chips, small avatars, toggle tracks) without needing per-widget
  /// math — `BorderRadius.circular(full)` on a widget shorter than this
  /// value always yields a true stadium/circle shape.
  static const double full = 999;

  static const BorderRadius radiusNone = BorderRadius.zero;
  static const BorderRadius radiusXs = BorderRadius.all(
    Radius.circular(xs),
  );
  static const BorderRadius radiusSm = BorderRadius.all(
    Radius.circular(sm),
  );
  static const BorderRadius radiusMd = BorderRadius.all(
    Radius.circular(md),
  );
  static const BorderRadius radiusLg = BorderRadius.all(
    Radius.circular(lg),
  );
  static const BorderRadius radiusFull = BorderRadius.all(
    Radius.circular(full),
  );
}
