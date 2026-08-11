import 'package:flutter/material.dart';

import '../../../design/design.dart';
import '../../../shared/presentation/widgets/not_connected_placeholder.dart';

/// Formula / Score Explanation — UX/UI Design Bible's "visible formula"
/// differentiator (Section 5.1: "The full recovery-score formula
/// breakdown is one tap away"; Section 12: "the formula breakdown is a
/// tap away on the same chart"). No numeric readiness score or recovery
/// band is computed or exposed by any endpoint: `ReadinessRuleEngine`
/// (backend `domain/readiness/rules/`) evaluates five real rules and
/// produces a real `RuleResult`, but no route returns it — only
/// `POST /api/v1/readiness` and the two `PUT` update routes return its
/// flattened `recommendations` as plain advisory strings (shown for real
/// on Readiness Home), never a score, a band, or a per-rule pass/fail
/// breakdown. Per this module's own explicit instruction — a Formula/
/// Score Explanation screen only if the backend exposes one — this
/// screen is a real, reachable, honest placeholder rather than either a
/// fabricated score or a silently missing menu item, the same posture
/// every other total gap in this app takes (`docs/adr/0040-readiness-
/// module.md`).
class ReadinessFormulaScreen extends StatelessWidget {
  const ReadinessFormulaScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(AppIcons.back),
          tooltip: 'Back',
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Recovery score'),
      ),
      body: const SafeArea(
        child: Center(
          child: NotConnectedPlaceholder(
            title: 'Recovery score not connected yet',
            message:
                'A combined readiness score with its formula breakdown '
                "needs a backend endpoint that doesn't exist yet. Your "
                'check-ins are real and saved either way — this screen is '
                'ready the moment that endpoint ships.',
          ),
        ),
      ),
    );
  }
}
