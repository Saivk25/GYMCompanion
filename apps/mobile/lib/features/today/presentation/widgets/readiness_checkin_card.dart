import 'package:flutter/material.dart';

import '../../../../design/design.dart';

/// The readiness check-in prompt — rendered above the session card
/// whenever today's check-in has not yet been submitted (UX/UI Design
/// Bible Section 5.1: "A not-yet-completed readiness check-in outranks
/// [the session card], appearing above [it] until submitted"). Once
/// submitted, this card disappears entirely; the resolved band moves to
/// the header's quiet status chip (`TodayScreen`'s own `_ReadinessBandChip`)
/// instead.
///
/// Deliberately plain — no icon, no color beyond the design system's
/// default card surface. This is a two-minute daily form, not a moment
/// this app is trying to make feel eventful; the outranking position
/// above the session card is what signals its priority, not decoration.
class ReadinessCheckInCard extends StatelessWidget {
  const ReadinessCheckInCard({required this.onStart, super.key});

  final VoidCallback onStart;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Text("Today's readiness check-in", style: textTheme.titleLarge),
          const SizedBox(height: AppSpacing.xs),
          Text(
            "A few quick questions set today's session tier.",
            style: textTheme.bodyMedium,
          ),
          const SizedBox(height: AppSpacing.lg),
          AppButton(label: 'Complete check-in', onPressed: onStart),
        ],
      ),
    );
  }
}
