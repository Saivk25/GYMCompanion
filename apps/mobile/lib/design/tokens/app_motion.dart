import 'package:flutter/widgets.dart';

/// Motion tokens — durations and curves, plus a reduced-motion-aware
/// helper. Per the UX/UI Design Bible (Section 10, 14): "purposeful only
/// — state-transition feedback, never decoration," "respects the OS
/// reduced-motion setting," "short and consistent."
///
/// ## Why every duration here is short
///
/// Premium, fast-feeling software (Linear and Arc are the two most
/// discussed examples for exactly this reason) is aggressively snappy —
/// motion finishes before the user has consciously registered a wait.
/// The instinct to add a slower, more "cinematic" transition to make an
/// interface feel polished is the opposite of what actually reads as
/// polish: a slow transition reads as latency, not craft, the moment a
/// user is doing something repeatedly (which describes nearly every
/// interaction in a daily-use fitness app). Nothing in this token set
/// exceeds 320ms; most real interactions should use [fast] or [normal].
///
/// ## Why no bounce/spring/elastic curve exists here
///
/// A bouncy overshoot curve is legible as "playful" or "gamified" —
/// appropriate for a casual mobile game, wrong for a product whose own
/// design principles explicitly reject "gaming dashboard" aesthetics and
/// unnecessary gamification (Bible Section 11). Every curve below
/// decelerates *into* its final state and never overshoots it — motion
/// that settles calmly reads as considered; motion that bounces reads as
/// decorative, which is the one thing this system's motion is
/// specifically told not to be.
abstract final class AppMotion {
  /// State that changes with no perceptible transition — a value that
  /// updates while off-screen, or a change so instantaneous that
  /// animating it would only slow down the interaction.
  static const Duration instant = Duration.zero;

  /// The default for small, frequent feedback — a button press, a toggle,
  /// a chip selection. Fast enough to feel like direct manipulation
  /// rather than an animated response to it.
  static const Duration fast = Duration(milliseconds: 120);

  /// The default for most transitions — a card expanding, a bottom sheet
  /// opening, a route change. Long enough to be perceived as motion
  /// (not a jump-cut), short enough to never feel like a wait.
  static const Duration normal = Duration(milliseconds: 200);

  /// Reserved for the largest on-screen transitions — a full-screen
  /// overlay entrance, a shared-element transition between a list and
  /// its detail view. This is the ceiling: nothing in this app should
  /// animate slower than this.
  static const Duration slow = Duration(milliseconds: 320);

  /// The standard easing for most transitions — decelerates into its
  /// final position, which reads as the motion "arriving" rather than
  /// stopping abruptly. Flutter's own [Curves.easeOutCubic]: well-tested,
  /// unsurprising, and exactly the "predictable" quality the Bible asks
  /// motion to have.
  static const Curve standard = Curves.easeOutCubic;

  /// A slightly more pronounced deceleration for larger transitions
  /// (bottom sheets, full-screen overlays) where the motion covers more
  /// visual distance and benefits from a more noticeable settle — still
  /// no overshoot, just a longer deceleration tail than [standard].
  static const Curve emphasized = Curves.easeOutQuart;

  /// Returns [requested], or [Duration.zero] when the OS reduced-motion
  /// accessibility setting is enabled. Every call site that starts a
  /// decorative-adjacent animation (anything beyond an unavoidable state
  /// change) should route its duration through this helper rather than
  /// using a token directly — motion is only ever "purposeful," per the
  /// Bible, when it can be turned off without losing information.
  static Duration resolve(BuildContext context, Duration requested) {
    final bool reduceMotion =
        MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    return reduceMotion ? Duration.zero : requested;
  }
}
