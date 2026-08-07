import 'package:flutter/material.dart';

import '../../../design/design.dart';
import '../../../shared/presentation/widgets/not_connected_placeholder.dart';

/// Photo Check-in Capture — UX/UI Design Bible Section 5.5: a live
/// camera view with an on-device alignment overlay and quality gate. No
/// photo field, model, or route exists anywhere in the backend (a grep
/// across the whole backend for photo/image/picture finds zero real
/// hits — the only mention is a doc-comment reference to this exact
/// Bible concept as an unbuilt sibling of `Progress`, see
/// `docs/adr/0039-progress-module.md`). A real, reachable screen with an
/// honest "not connected yet" placeholder, the same posture
/// `LogMealScreen`'s Photo mode already established for Fuel — never
/// silently omitted from Transformation's own navigation.
class PhotoCheckinScreen extends StatelessWidget {
  const PhotoCheckinScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(AppIcons.back),
          tooltip: 'Back',
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Photo check-in'),
      ),
      body: const SafeArea(
        child: Center(
          child: NotConnectedPlaceholder(
            title: 'Photo check-in not connected yet',
            message:
                'Guided capture with on-device alignment and quality '
                "checking needs a backend endpoint that doesn't exist yet. "
                'Log measurements in the meantime — your weight and '
                'circumference trends stay real either way.',
          ),
        ),
      ),
    );
  }
}
