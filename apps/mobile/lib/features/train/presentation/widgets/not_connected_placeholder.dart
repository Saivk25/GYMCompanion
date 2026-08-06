import 'package:flutter/material.dart';

import '../../../../design/design.dart';

/// The shared, honest "this feature isn't wired to a real backend yet"
/// placeholder — used by the Library tab (`TrainHomeScreen`),
/// `ExerciseDetailScreen`'s cues/history section, and
/// `PersonalRecordsScreen`. Deliberately distinct from an ordinary empty
/// state ([AppEmptyState] alone, used e.g. for "no sessions planned this
/// week"): those describe a normal, expected absence of *data*; this one
/// discloses an absence of *capability* — no backend endpoint exists yet
/// for this feature at all, not merely "nothing here right now." Per this
/// project's own directive: "If backend functionality is unavailable,
/// show an honest, polished placeholder explaining that the feature is
/// not yet connected" — this is that placeholder, built once and reused,
/// rather than three screens each inventing their own wording.
///
/// Still built entirely from [AppEmptyState] — no new visual language,
/// only a specific icon/title/message combination reused consistently.
class NotConnectedPlaceholder extends StatelessWidget {
  const NotConnectedPlaceholder({
    required this.title,
    required this.message,
    super.key,
  });

  final String title;
  final String message;

  @override
  Widget build(BuildContext context) {
    return AppEmptyState(
      icon: AppIcons.info,
      title: title,
      message: message,
    );
  }
}
