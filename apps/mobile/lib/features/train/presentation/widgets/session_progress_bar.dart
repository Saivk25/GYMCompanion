import 'package:flutter/material.dart';

import '../../../../design/design.dart';

/// A slim completion meter — shared between the Active Workout screen
/// ("Session Progress", tracking exercises completed so far) and Session
/// Summary (the final completion percentage). One small, reusable
/// widget rather than two screens each drawing their own bar, per this
/// project's "reuse whenever possible" instruction.
class SessionProgressBar extends StatelessWidget {
  const SessionProgressBar({required this.fraction, super.key});

  /// 0.0-1.0. Values outside that range are clamped, never asserted —
  /// a slightly-over-100% completion estimate should visually cap, not
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
