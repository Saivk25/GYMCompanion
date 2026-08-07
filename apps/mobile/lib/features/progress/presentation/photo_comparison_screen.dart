import 'package:flutter/material.dart';

import '../../../design/design.dart';
import '../../../shared/presentation/widgets/not_connected_placeholder.dart';

/// Photo comparison viewer — UX/UI Design Bible's "side-by-side,
/// synced-pose comparison" (Section 5.11 catalog; Section 12: "never an
/// auto-generated overlay morph — that would imply false precision the
/// product explicitly avoids"). Depends entirely on Photo Check-in
/// Capture's own captured photos existing first, which they don't — no
/// photo concept exists anywhere in the backend. A real, reachable
/// screen with an honest placeholder, not a hidden or skipped one.
class PhotoComparisonScreen extends StatelessWidget {
  const PhotoComparisonScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(AppIcons.back),
          tooltip: 'Back',
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Compare photos'),
      ),
      body: const SafeArea(
        child: Center(
          child: NotConnectedPlaceholder(
            title: 'Photo comparison not connected yet',
            message:
                'Comparing two check-in photos side by side needs the same '
                "backend photo capability photo check-in does, and neither "
                'exists yet. Your measurement trends are real in the '
                'meantime.',
          ),
        ),
      ),
    );
  }
}
