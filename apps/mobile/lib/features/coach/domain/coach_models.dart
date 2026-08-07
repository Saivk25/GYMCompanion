/// Pure Dart view types for the Coach module — no Flutter import
/// anywhere in this file, matching every other feature's own `domain/`
/// rule. Coach's one real data source, [CoachSignal], is defined in
/// `lib/shared/domain/coach_signal.dart`, not here — see that file's own
/// doc comment for why it had to be shared from the start rather than
/// promoted later.
library;

import '../../../shared/domain/coach_signal.dart';

/// The complete state Coach Home renders from once its initial read of
/// the shared signal log has resolved. Mirrors every other module's own
/// `*HomeViewState` shape (a single page-level `AsyncValue`, no nested
/// per-card status enum) for consistency, even though Coach's own
/// "fetch" is a read of in-memory client state rather than a network
/// call — see `CoachRepository`'s own doc comment.
class CoachHomeViewState {
  const CoachHomeViewState({
    required this.asOf,
    this.signals = const <CoachSignal>[],
    this.isOffline = false,
  });

  final DateTime asOf;

  /// Every real signal captured so far this session, newest first.
  /// Empty on a fresh app launch — not an error state, and not "still
  /// loading": a user who hasn't logged a check-in, a meal, or a
  /// completed session yet this session has genuinely generated nothing
  /// for Coach to show, the same honest distinction
  /// `ReadinessHomeViewState.hasCheckedInEver` draws for a first-time
  /// user.
  final List<CoachSignal> signals;

  final bool isOffline;

  bool get hasAnySignals => signals.isNotEmpty;

  /// Filters to one [CoachModule] (Recovery/Nutrition/Training advice),
  /// or the full list when [module] is `null` (the "All" segment) —
  /// pure filtering over already-real data, never a second data source.
  List<CoachSignal> forModule(CoachModule? module) {
    if (module == null) return signals;
    return signals.where((CoachSignal s) => s.module == module).toList();
  }
}
