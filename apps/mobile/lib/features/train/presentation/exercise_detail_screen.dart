import 'package:flutter/material.dart';

import '../../../design/design.dart';
import 'widgets/not_connected_placeholder.dart';

/// Exercise Detail — UX/UI Design Bible catalog: "Cues, video, personal
/// history for one movement. Return to session or browse freely."
///
/// A real, reachable screen (linked from Active Workout's "Cues"
/// action) — not skipped — but everything below the exercise's own name
/// is an honest "not connected yet" placeholder: no backend endpoint
/// resolves an exercise id to cues, video, or per-exercise history today
/// (`backend/app/api/routes/v1/` has no `exercise.py` route file at all;
/// see `train_models.dart`'s own doc comment on the same gap for
/// `exerciseName`). [exerciseName] itself is real — whatever the caller
/// already knew when navigating here — this screen does not pretend to
/// know more than that.
class ExerciseDetailScreen extends StatelessWidget {
  const ExerciseDetailScreen({required this.exerciseId, required this.exerciseName, super.key});

  final String exerciseId;
  final String? exerciseName;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(AppIcons.back),
          tooltip: 'Back',
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: Text(exerciseName ?? 'Exercise'),
      ),
      body: SafeArea(
        child: Center(
          child: NotConnectedPlaceholder(
            title: 'Cues and history not connected yet',
            message: exerciseName == null
                ? "This exercise's cues, video, and personal history need "
                    "a backend endpoint that doesn't exist yet."
                : 'Cues, video, and your personal history for '
                    '$exerciseName need a backend endpoint that '
                    "doesn't exist yet. This screen is ready — it's "
                    'wired up the moment that endpoint ships.',
          ),
        ),
      ),
    );
  }
}
