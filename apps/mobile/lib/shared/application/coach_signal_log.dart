import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/coach_signal.dart';

/// The one piece of genuinely cross-feature *mutable* state in this
/// codebase — every other shared type (`SessionTier`,
/// `NotConnectedPlaceholder`) is a value type or a stateless widget.
/// This is a small, deliberate exception, and exists for one reason:
/// Coach has no backend endpoint of its own to fetch from (see
/// `docs/adr/0041-coach-module.md`'s research section — no aggregation
/// endpoint exists, or is implied by the current API design, because
/// every rule engine's output is returned only once, synchronously, on
/// the exact mutating call that triggered it). The only way Coach can
/// ever show real, non-fabricated cross-module guidance is by reading
/// what Readiness/Fuel/Train's own controllers already receive from
/// their own real backend calls, at the moment they receive it — this
/// log is that one shared place.
///
/// [CoachSignalLog] is intentionally the simplest thing that could work:
/// an in-memory list, newest-first, reset on every app restart (like
/// every mock repository's own state in this codebase), with no
/// persistence and no backend counterpart. It is not a repository and
/// does not pretend to be one — nothing here will ever be replaced by
/// an HTTP client, because there is no HTTP endpoint for this data to
/// come from instead. Compare `MockCoachRepository`
/// (`features/coach/infrastructure/mock_coach_repository.dart`), which
/// reads this log and *does* follow the "swap for a real repository
/// later" shape, since Coach's own read side is written generically
/// against a `CoachRepository` interface for architectural consistency
/// with every other module — see that file's own doc comment for why
/// that distinction matters.
class CoachSignalLog extends Notifier<List<CoachSignal>> {
  int _nextId = 0;

  @override
  List<CoachSignal> build() => const <CoachSignal>[];

  /// Parses every real `"[severity] message"` string a module's own
  /// controller just received from its repository into a [CoachSignal]
  /// and prepends them (newest first). A call with an empty [rawWarnings]
  /// is a normal no-op, not an error — most real actions trigger no
  /// rule at all (`RuleResult.recommendations` is `()` far more often
  /// than not), and Coach must never treat "nothing to report" as
  /// something to fabricate a signal about.
  ///
  /// "Newest first" applies across separate [add] calls (this call's
  /// signals go before whatever [state] already held) — it does not mean
  /// reversing the order *within* one call's own [rawWarnings], which
  /// would scramble the relative order two warnings from the same rule
  /// engine run were produced in.
  void add(CoachModule module, List<String> rawWarnings) {
    if (rawWarnings.isEmpty) return;
    final DateTime now = DateTime.now();
    final List<CoachSignal> parsed = <CoachSignal>[
      for (final String raw in rawWarnings)
        CoachSignal.parse(
          id: 'signal-${_nextId++}',
          module: module,
          raw: raw,
          occurredAt: now,
        ),
    ];
    state = <CoachSignal>[...parsed, ...state];
  }
}

final NotifierProvider<CoachSignalLog, List<CoachSignal>> coachSignalLogProvider =
    NotifierProvider<CoachSignalLog, List<CoachSignal>>(CoachSignalLog.new);
