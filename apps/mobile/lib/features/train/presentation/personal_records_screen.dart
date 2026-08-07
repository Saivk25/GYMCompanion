import 'package:flutter/material.dart';

import '../../../design/design.dart';
import '../../../shared/presentation/widgets/not_connected_placeholder.dart';

/// Personal Records — UX/UI Design Bible catalog: "All personal records.
/// Open a PR's history." A real, reachable screen (Train Home links here
/// in a future pass; reachable directly today via its route) with an
/// honest "not connected yet" placeholder — no dedicated PR endpoint
/// exists in `backend/app/api/routes/v1/progress.py` (only generic
/// progress-record CRUD), and computing a genuine PR needs cross-session
/// aggregation this project's implementation order has not reached yet.
/// `TrainPersonalRecord` (`domain/train_models.dart`) is modeled ahead of
/// that work so a future real repository has a shape to fill in, but
/// nothing constructs one today — inventing plausible-looking PR numbers
/// here would be exactly the "no fake data, no fake success" this
/// project's own directive forbids.
class PersonalRecordsScreen extends StatelessWidget {
  const PersonalRecordsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(AppIcons.back),
          tooltip: 'Back',
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Personal records'),
      ),
      body: const SafeArea(
        child: Center(
          child: NotConnectedPlaceholder(
            title: 'Personal records not connected yet',
            message:
                'Tracking your all-time bests needs a backend endpoint '
                "that doesn't exist yet. This screen is ready — it's "
                'wired up the moment that endpoint ships.',
          ),
        ),
      ),
    );
  }
}
