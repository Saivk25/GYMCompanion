import 'package:flutter/widgets.dart';

/// Responsive breakpoints and the resulting window size class.
///
/// The three widths below (0, 600, 840) are not invented for this app —
/// they are Material 3's own published adaptive-layout window-size-class
/// boundaries (compact / medium / expanded). Reusing an established,
/// externally-documented standard rather than picking round numbers
/// ourselves means this scale is already validated against real device
/// sizes across phones, small tablets, and large tablets, and it matches
/// what [MediaQuery]-based Flutter tooling and documentation already
/// assume — a future contributor researching "Flutter breakpoints" finds
/// this exact scale, not a bespoke one to relearn.
///
/// The UX/UI Design Bible (Section 17) scopes desktop out of MVP and
/// treats phone as the primary target, with tablet adopting a
/// master-detail/rail pattern for Progress and Coach specifically — not
/// a full independent desktop layout system. [WindowSizeClass.expanded]
/// exists in this scale today because the boundary is free to define
/// now and costly to retrofit later, even though no screen built in this
/// phase yet branches on it.
enum WindowSizeClass {
  /// Phone, portrait or landscape. The primary target — every screen in
  /// this app must work correctly here first.
  compact,

  /// A small/medium tablet, or a large phone in landscape. Progress and
  /// Coach adopt a two-pane master-detail layout at this size and above
  /// (Bible Section 17); most other screens are unaffected and simply
  /// gain wider margins.
  medium,

  /// A large tablet, or (future, out of MVP scope) desktop. The bottom
  /// tab bar becomes a left navigation rail at this size and above.
  expanded,
}

abstract final class AppBreakpoints {
  static const double medium = 600;
  static const double expanded = 840;

  static WindowSizeClass classify(double width) {
    if (width >= expanded) {
      return WindowSizeClass.expanded;
    }
    if (width >= medium) {
      return WindowSizeClass.medium;
    }
    return WindowSizeClass.compact;
  }
}

/// `context.windowSizeClass` — the idiomatic call site for breakpoint
/// checks, so a screen never re-derives the classification logic itself.
extension WindowSizeClassContext on BuildContext {
  WindowSizeClass get windowSizeClass {
    final double width = MediaQuery.sizeOf(this).width;
    return AppBreakpoints.classify(width);
  }
}
