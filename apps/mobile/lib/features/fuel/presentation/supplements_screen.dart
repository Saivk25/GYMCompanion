import 'package:flutter/material.dart';

import '../../../design/design.dart';
import '../../../shared/presentation/widgets/not_connected_placeholder.dart';

/// Supplement log/schedule — no supplement domain concept exists
/// anywhere in the backend (no aggregate, no endpoint, not even a field
/// on `Nutrition`). A real, reachable screen with an honest "not
/// connected yet" placeholder, the same posture Train's Personal Records
/// screen already established for a comparably total backend gap.
class SupplementsScreen extends StatelessWidget {
  const SupplementsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(AppIcons.back),
          tooltip: 'Back',
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Supplements'),
      ),
      body: const SafeArea(
        child: Center(
          child: NotConnectedPlaceholder(
            title: 'Supplement tracking not connected yet',
            message:
                'Dose and schedule tracking needs backend support that '
                "doesn't exist yet. This screen is ready — it's wired up "
                'the moment that support ships.',
          ),
        ),
      ),
    );
  }
}
