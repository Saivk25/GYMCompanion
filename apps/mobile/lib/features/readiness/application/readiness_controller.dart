import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/readiness_models.dart';

/// The seam between Readiness's presentation layer and wherever its data
/// actually comes from — mirrors `ProgressRepository`'s/`FuelRepository`'s
/// own role exactly. [submitCheckIn] maps to `POST /api/v1/readiness`
/// (`RecordReadinessRequest`) with whichever of the six inputs the user
/// filled in populated, matching `RecordReadinessHandler`'s real
/// behavior of evaluating `ReadinessRuleEngine` once, after commit, and
/// surfacing its recommendations as warnings
/// (`docs/adr/0040-readiness-module.md`) — the real, non-fabricated
/// source [ReadinessCheckInResult.warnings] carries.
///
/// There is deliberately no method here for a computed readiness score
/// or recovery band — no endpoint returns one (`ReadinessResponse`
/// exposes only the six raw inputs), so `ReadinessFormulaScreen` renders
/// a disclosed "not connected yet" state directly, the same posture
/// `TrainRepository`/`FuelRepository`/`ProgressRepository` already
/// established for their own total gaps.
abstract interface class ReadinessRepository {
  Future<ReadinessHomeViewState> fetchHome();

  Future<ReadinessCheckInResult> submitCheckIn({
    required DateTime date,
    Duration? sleepDuration,
    int? sleepQuality,
    int? energyLevel,
    int? stressLevel,
    int? sorenessLevel,
    double? restingHeartRate,
    double? heartRateVariability,
    String? notes,
  });
}

/// No default implementation — the same "throw until overridden" posture
/// every other repository provider in this app uses.
final Provider<ReadinessRepository> readinessRepositoryProvider =
    Provider<ReadinessRepository>(
  (ref) => throw UnimplementedError(
    'readinessRepositoryProvider has no default implementation — see '
    'lib/main.dart, which overrides it with MockReadinessRepository '
    'until a real API-backed repository exists.',
  ),
);

/// Readiness Home's page-level fetch lifecycle, plus its one logging
/// action. Mirrors `ProgressHomeController`/`FuelHomeController` exactly:
/// [submitCheckIn] does *not* guard into `state` on failure (a failed
/// check-in should not blank the whole page behind a full-page error —
/// `ReadinessCheckInScreen` catches locally and shows a `SnackBar`), then
/// re-fetches on success and folds the just-returned warnings into the
/// new state rather than hand-merging the new entry into local state.
class ReadinessHomeController extends AsyncNotifier<ReadinessHomeViewState> {
  @override
  Future<ReadinessHomeViewState> build() {
    return ref.read(readinessRepositoryProvider).fetchHome();
  }

  Future<void> refresh() async {
    state = const AsyncValue<ReadinessHomeViewState>.loading();
    state = await AsyncValue.guard(
      () => ref.read(readinessRepositoryProvider).fetchHome(),
    );
  }

  Future<ReadinessCheckInResult> submitCheckIn({
    required DateTime date,
    Duration? sleepDuration,
    int? sleepQuality,
    int? energyLevel,
    int? stressLevel,
    int? sorenessLevel,
    double? restingHeartRate,
    double? heartRateVariability,
    String? notes,
  }) async {
    final ReadinessCheckInResult result = await ref.read(readinessRepositoryProvider).submitCheckIn(
          date: date,
          sleepDuration: sleepDuration,
          sleepQuality: sleepQuality,
          energyLevel: energyLevel,
          stressLevel: stressLevel,
          sorenessLevel: sorenessLevel,
          restingHeartRate: restingHeartRate,
          heartRateVariability: heartRateVariability,
          notes: notes,
        );
    final ReadinessHomeViewState refreshed =
        await ref.read(readinessRepositoryProvider).fetchHome();
    state = AsyncValue<ReadinessHomeViewState>.data(
      ReadinessHomeViewState(
        asOf: refreshed.asOf,
        entries: refreshed.entries,
        hasCheckedInEver: refreshed.hasCheckedInEver,
        lastCheckInWarnings: result.warnings,
        isOffline: refreshed.isOffline,
      ),
    );
    return result;
  }
}

final AsyncNotifierProvider<ReadinessHomeController, ReadinessHomeViewState>
    readinessHomeControllerProvider =
    AsyncNotifierProvider<ReadinessHomeController, ReadinessHomeViewState>(
  ReadinessHomeController.new,
);
