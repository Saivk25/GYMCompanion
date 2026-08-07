import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/progress_models.dart';

/// The seam between Progress's presentation layer and wherever its data
/// actually comes from — mirrors `FuelRepository`'s/`TrainRepository`'s
/// own role exactly. [logMeasurement] maps to `POST /api/v1/progress`
/// (`RecordProgressRequest`) with whichever body-composition/measurement
/// fields the user filled in populated; the backend's split between
/// `PUT .../body-composition` and `PUT .../measurements` is an *update*
/// path for an existing entry, not something this client's
/// append-only-in-practice logging flow needs — see
/// `docs/adr/0039-progress-module.md`.
///
/// [fetchHome] alone supplies every real surface Progress Home renders:
/// recent measurements (for the Transformation dashboard and its
/// trend-detail drill-in), a week of real nutrition totals (for the
/// Nutrition dashboard), and a week of real raw readiness inputs (for the
/// Recovery dashboard's trend lines). There is deliberately no method
/// here for workout analytics, reports, photos, or correlation
/// insights — no backend endpoint exists for any of them
/// (`backend/app/api/routes/v1/` has no analytics, report, photo, or
/// correlation route at all), so those sections of `ProgressHomeScreen`
/// render `NotConnectedPlaceholder` directly, the same posture
/// `TrainRepository`/`FuelRepository` already established for their own
/// total gaps.
abstract interface class ProgressRepository {
  Future<ProgressHomeViewState> fetchHome();

  Future<ProgressEntry> logMeasurement({
    required DateTime date,
    double? bodyWeight,
    double? bodyFatPercentage,
    double? leanBodyMass,
    double? muscleMass,
    double? waist,
    double? chest,
    double? hip,
    double? arm,
    double? thigh,
    double? calf,
    double? neck,
    String? notes,
  });
}

/// No default implementation — the same "throw until overridden" posture
/// [fuelRepositoryProvider]/[trainRepositoryProvider] use.
final Provider<ProgressRepository> progressRepositoryProvider =
    Provider<ProgressRepository>(
  (ref) => throw UnimplementedError(
    'progressRepositoryProvider has no default implementation — see '
    'lib/main.dart, which overrides it with MockProgressRepository '
    'until a real API-backed repository exists.',
  ),
);

/// Progress Home's page-level fetch lifecycle, plus its one logging
/// action. Mirrors `FuelHomeController` exactly: [logMeasurement] does
/// *not* guard into `state` on failure (a failed log should not blank
/// the whole page behind a full-page error — `LogMeasurementScreen`
/// catches locally and shows a `SnackBar`), then re-fetches on success
/// rather than hand-merging the new entry into local state.
class ProgressHomeController extends AsyncNotifier<ProgressHomeViewState> {
  @override
  Future<ProgressHomeViewState> build() {
    return ref.read(progressRepositoryProvider).fetchHome();
  }

  Future<void> refresh() async {
    state = const AsyncValue<ProgressHomeViewState>.loading();
    state = await AsyncValue.guard(
      () => ref.read(progressRepositoryProvider).fetchHome(),
    );
  }

  Future<void> logMeasurement({
    required DateTime date,
    double? bodyWeight,
    double? bodyFatPercentage,
    double? leanBodyMass,
    double? muscleMass,
    double? waist,
    double? chest,
    double? hip,
    double? arm,
    double? thigh,
    double? calf,
    double? neck,
    String? notes,
  }) async {
    await ref.read(progressRepositoryProvider).logMeasurement(
          date: date,
          bodyWeight: bodyWeight,
          bodyFatPercentage: bodyFatPercentage,
          leanBodyMass: leanBodyMass,
          muscleMass: muscleMass,
          waist: waist,
          chest: chest,
          hip: hip,
          arm: arm,
          thigh: thigh,
          calf: calf,
          neck: neck,
          notes: notes,
        );
    state = await AsyncValue.guard(
      () => ref.read(progressRepositoryProvider).fetchHome(),
    );
  }
}

final AsyncNotifierProvider<ProgressHomeController, ProgressHomeViewState>
    progressHomeControllerProvider =
    AsyncNotifierProvider<ProgressHomeController, ProgressHomeViewState>(
  ProgressHomeController.new,
);
