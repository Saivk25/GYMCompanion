import 'package:flutter/material.dart';

import '../../../design/design.dart';
import '../../../shared/presentation/widgets/not_connected_placeholder.dart';

/// Coaching History — UX/UI Design Bible's named Coach screen, for
/// looking back at guidance from *previous* sessions (as distinct from
/// Coach Home's "Recent guidance" feed, which is real but explicitly
/// this-session-only — see `CoachSignalLog`'s own doc comment). No
/// backend endpoint persists rule-engine output at all: every
/// `Recommendation` a rule engine produces is returned once, in the
/// same HTTP response as the mutation that triggered it, and never
/// written anywhere the backend could read it back from later
/// (`docs/adr/0041-coach-module.md`'s research section). A real history
/// would need the backend to persist recommendations against a user and
/// expose a query for them — neither exists today. Per this module's
/// own directive, this is a real, reachable, honest placeholder rather
/// than a fabricated log or a silently missing menu item.
class CoachHistoryScreen extends StatelessWidget {
  const CoachHistoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(AppIcons.back),
          tooltip: 'Back',
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Coaching history'),
      ),
      body: const SafeArea(
        child: Center(
          child: NotConnectedPlaceholder(
            title: 'Coaching history not connected yet',
            message:
                'Past guidance needs the backend to save recommendations '
                "against your account, which doesn't happen yet — nothing "
                'from a previous app session is available to look back on. '
                "This session's own guidance is still real, on Coach Home.",
          ),
        ),
      ),
    );
  }
}
