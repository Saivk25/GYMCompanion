import 'package:flutter/material.dart';

import '../tokens/tokens.dart';

/// A slim, flat completion meter — this app's one progress-bar
/// component. Originally built scoped to Train's Active Workout/Session
/// Summary screens (as `SessionProgressBar`); promoted here once Fuel's
/// hydration progress needed the identical shape a second time, per this
/// project's own "if duplication appears, improve the design system,
/// not the screen" rule. No gradient, no rounded pill glow, no
/// animation on value change — a flat two-tone bar, matching this
/// system's "no decorative charts" standing constraint.
class AppProgressBar extends StatelessWidget {
  const AppProgressBar({required this.fraction, super.key});

  /// 0.0-1.0. Values outside that range are clamped, never asserted —
  /// a slightly-over-100% total (more water logged than the day's
  /// target, more sets completed than planned) should visually cap, not
  /// crash.
  final double fraction;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final double clamped = fraction.clamp(0.0, 1.0);

    return ClipRRect(
      borderRadius: AppRadius.radiusFull,
      child: SizedBox(
        height: 6,
        child: Stack(
          children: <Widget>[
            ColoredBox(color: colorScheme.surfaceContainerHighest),
            FractionallySizedBox(
              widthFactor: clamped,
              child: ColoredBox(color: colorScheme.primary),
            ),
          ],
        ),
      ),
    );
  }
}
