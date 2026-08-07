import 'package:flutter/material.dart';

import '../../../design/design.dart';

/// The shared, honest "this feature isn't wired to a real backend yet"
/// placeholder. Originally built scoped to Train (its Library tab,
/// Exercise Detail's cues/history section, Personal Records); promoted
/// to `lib/shared/presentation/` once Fuel needed the identical pattern
/// a second time (Food Search, Supplements) — per this project's own
/// "if duplication appears, improve the design system, not the screen"
/// rule, applied here to a cross-feature widget rather than a
/// `lib/design/` primitive, since this is a specific *product* messaging
/// convention (what "not connected" means and how it's worded), not a
/// generic visual token or component every screen might need.
///
/// Deliberately distinct from an ordinary empty state ([AppEmptyState]
/// alone, used e.g. for "no sessions planned this week"): those describe
/// a normal, expected absence of *data*; this one discloses an absence
/// of *capability* — no backend endpoint exists yet for this feature at
/// all, not merely "nothing here right now." Per this project's own
/// directive: "If backend functionality is unavailable, show an honest,
/// polished placeholder explaining that the feature is not yet
/// connected" — this is that placeholder, built once and reused, rather
/// than every screen inventing its own wording.
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
