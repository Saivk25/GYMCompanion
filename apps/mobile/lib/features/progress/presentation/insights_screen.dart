import 'package:flutter/material.dart';

import '../../../design/design.dart';
import '../../../shared/presentation/widgets/not_connected_placeholder.dart';

/// Insight/correlation detail — UX/UI Design Bible's "one surfaced
/// correlation, expanded" (Section 5.11 catalog; Section 12: "a scatter
/// plot with a trend line, shown only once minimum sample size is met.
/// Below the threshold, an explicit 'not enough data yet' placeholder
/// replaces the chart entirely"). This screen's gap is a different kind
/// than a sample-size shortfall, though: no correlation or insight logic
/// exists anywhere in the backend domain layer at all (`domain/progress/
/// rules/` has only a threshold-based measurement-trend detector, no
/// cross-domain correlation concept), so no amount of logged history
/// would produce one yet. A real, reachable screen with an honest
/// placeholder rather than a silently absent menu item.
class InsightsScreen extends StatelessWidget {
  const InsightsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(AppIcons.back),
          tooltip: 'Back',
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Correlations'),
      ),
      body: const SafeArea(
        child: Center(
          child: NotConnectedPlaceholder(
            title: 'Correlations not connected yet',
            message:
                'Surfacing a real correlation — like how sleep relates to '
                'training performance — needs backend statistics logic '
                "that doesn't exist yet. The trends on each dashboard "
                'above are your real logged data in the meantime.',
          ),
        ),
      ),
    );
  }
}
