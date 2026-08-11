import 'package:flutter/foundation.dart' show listEquals;
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/application/coach_signal_log.dart';
import '../../../shared/domain/coach_signal.dart';
import '../domain/coach_models.dart';

/// The seam between Coach's presentation layer and wherever its data
/// actually comes from — the same architectural shape every other
/// module's own repository interface follows (`TodayRepository`,
/// `TrainRepository`, `FuelRepository`, `ProgressRepository`,
/// `ReadinessRepository`), for consistency, even though what backs it is
/// unlike any of theirs.
///
/// ## This is not "mock until a real backend arrives"
///
/// Every other repository in this codebase throws by default specifically
/// because a real, HTTP-backed implementation is expected to eventually
/// override it (see each one's own provider doc comment). [fetchRecent
/// Signals] has no such future: there is no backend endpoint that
/// aggregates advisory output across modules, and the current API design
/// gives no reason to expect one — every rule engine's `recommendations`
/// are returned exactly once, synchronously, on the specific mutating
/// call that produced them (`docs/adr/0041-coach-module.md`'s research
/// section). [MockCoachRepository] (`features/coach/infrastructure/
/// mock_coach_repository.dart`) is not a stand-in for a future HTTP
/// client; it reads the same session-scoped `CoachSignalLog`
/// (`lib/shared/application/coach_signal_log.dart`) every real mutation
/// elsewhere in this app already writes real, non-fabricated advisory
/// text into. The interface still exists — and still throws unless
/// overridden — for architectural consistency and testability (a widget
/// test can substitute a fake exactly like every other module's tests
/// already do), not because a network implementation is coming later.
abstract interface class CoachRepository {
  Future<List<CoachSignal>> fetchRecentSignals();
}

/// No default implementation — the same "throw until overridden" posture
/// every other repository provider in this app uses.
final Provider<CoachRepository> coachRepositoryProvider = Provider<CoachRepository>(
  (ref) => throw UnimplementedError(
    'coachRepositoryProvider has no default implementation — see '
    'lib/main.dart, which overrides it with MockCoachRepository '
    'until a real API-backed repository exists.',
  ),
);

/// Coach Home's page-level fetch lifecycle. Unlike every other
/// `*HomeController`, this one also [ref.listen]s the shared
/// `coachSignalLogProvider` and invalidates itself whenever it changes —
/// the first genuinely reactive cross-provider dependency in this
/// codebase. Without it, a signal captured while the Coach tab isn't
/// mounted (e.g. submitting a Readiness check-in from Today) would never
/// appear until some other event happened to rebuild this controller;
/// Coach's entire purpose is surfacing guidance the moment it becomes
/// real, so staying silently stale until a manual pull-to-refresh would
/// undercut the point of the feature.
class CoachHomeController extends AsyncNotifier<CoachHomeViewState> {
  @override
  Future<CoachHomeViewState> build() {
    ref.listen<List<CoachSignal>>(coachSignalLogProvider, (previous, next) {
      // Content equality, not reference equality: `coachSignalLogProvider`
      // can hand back a new list instance whose contents are unchanged
      // (e.g. the initial `const <CoachSignal>[]`), and a `previous !=
      // next` reference check would invalidate this controller on every
      // such rebuild — an unnecessary, and in a screen also watched by
      // `CoachSignalDetailScreen`, potentially compounding re-fetch.
      if (previous == null || !listEquals(previous, next)) {
        ref.invalidateSelf();
      }
    });
    return _fetch();
  }

  Future<void> refresh() async {
    state = const AsyncValue<CoachHomeViewState>.loading();
    state = await AsyncValue.guard(_fetch);
  }

  Future<CoachHomeViewState> _fetch() async {
    final List<CoachSignal> signals = await ref.read(coachRepositoryProvider).fetchRecentSignals();
    return CoachHomeViewState(asOf: DateTime.now(), signals: signals);
  }
}

final AsyncNotifierProvider<CoachHomeController, CoachHomeViewState> coachHomeControllerProvider =
    AsyncNotifierProvider<CoachHomeController, CoachHomeViewState>(CoachHomeController.new);
