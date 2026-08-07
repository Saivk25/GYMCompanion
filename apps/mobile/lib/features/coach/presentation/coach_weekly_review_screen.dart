import 'package:flutter/material.dart';

import '../../../design/design.dart';
import '../../../shared/presentation/widgets/not_connected_placeholder.dart';

/// Weekly Review — UX/UI Design Bible's named Coach screen. Research
/// found no backend concept this could honestly render: there is no
/// weekly-rollup, digest, or report endpoint anywhere in the backend
/// (`docs/adr/0039-progress-module.md` already confirmed zero "report"
/// hits across the whole codebase; this phase's own research confirms
/// the same is true for any per-week aggregation of rule-engine output
/// specifically). A client-side "count of this week's signals" could be
/// computed from the shared signal log, but every signal already in
/// that log was captured *this session* only (nothing persists across
/// app restarts, and nothing is queryable for a day the app wasn't
/// open) — a "weekly" review built from that data would silently mislead
/// by implying a real multi-day rollup that isn't actually there. Per
/// this module's own directive — a real, reachable, honest placeholder
/// rather than either a fabricated summary or a silently missing menu
/// item — this screen renders [NotConnectedPlaceholder], the same
/// posture every other total gap in this app takes
/// (`docs/adr/0041-coach-module.md`).
class CoachWeeklyReviewScreen extends StatelessWidget {
  const CoachWeeklyReviewScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(AppIcons.back),
          tooltip: 'Back',
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Weekly review'),
      ),
      body: const SafeArea(
        child: Center(
          child: NotConnectedPlaceholder(
            title: 'Weekly review not connected yet',
            message:
                'A real week-over-week summary needs a backend rollup '
                "endpoint that doesn't exist yet. Recent guidance on Coach "
                'Home is real and current — this screen is ready the '
                "moment that endpoint ships.",
          ),
        ),
      ),
    );
  }
}
