import 'package:flutter/material.dart';

/// Placeholder for the Today tab. Real content lands per the Engineering
/// Master Plan's sprint sequence — see docs/Gym_Companion_Engineering_Master_Plan.docx
/// Section 5 for exactly which sprint populates this screen, and
/// docs/Gym_Companion_UX_UI_Design_Bible.docx Section 5 for its full
/// specification once it's built for real.
class TodayScreen extends StatelessWidget {
  const TodayScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text('Today', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 8),
          Text(
            'The daily hub lands in Sprint 4-5.',
            style: Theme.of(context).textTheme.bodyMedium,
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}
