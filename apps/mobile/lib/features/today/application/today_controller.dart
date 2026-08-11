import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/today_models.dart';

/// The seam between Today's presentation layer and wherever its data
/// actually comes from — an abstract interface, per the Engineering
/// Master Plan's Clean Architecture separation applied to the client
/// (Presentation depends on this abstraction, never on a concrete HTTP
/// client or database directly).
///
/// The real implementation (an authenticated backend fetch, following the
/// same repository pattern `backend/app/application/`'s own use cases
/// already establish) does not exist yet — the API client, local cache,
/// and offline-sync layers are later, separately-scoped stages of the
/// implementation order this project is following, not part of building
/// one screen. [MockTodayRepository] (`../infrastructure/
/// mock_today_repository.dart`) is today's only implementation, and is
/// documented there, honestly, as a placeholder — the same disclosed-
/// limitation posture ADR 0002 already established for Flutter
/// verification generally, applied here to a missing data layer instead
/// of a missing SDK.
abstract interface class TodayRepository {
  Future<TodayViewState> fetchToday();
}

/// `Provider`, not a hardcoded `MockTodayRepository()` reference inside
/// [TodayController] — swapping in a real repository later (or an
/// integration test's fake) is an override on this one provider, not a
/// find-and-replace through the controller.
final Provider<TodayRepository> todayRepositoryProvider =
    Provider<TodayRepository>((ref) => throw UnimplementedError(
          'todayRepositoryProvider has no default implementation — see '
          'lib/main.dart, which overrides it with MockTodayRepository '
          'until a real API-backed repository exists.',
        ),
    );

/// Owns Today's page-level fetch lifecycle. Deliberately thin — an
/// [AsyncNotifier] whose only job is calling [TodayRepository.fetchToday]
/// and re-exposing the result; every per-card state
/// ([SessionCardStatus], the readiness band, the streak, the task) is
/// data already shaped by [TodayViewState] itself, not logic this
/// controller re-derives. Matches the UX/UI Design Bible's own layering:
/// [AsyncValue.loading]/`.error` here drive the *page's* skeleton/retry
/// (a genuine full-page fetch failure); [TodayViewState.sessionStatus]
/// separately drives the *session card's* own loading/empty/error/
/// success states once the page itself has data.
class TodayController extends AsyncNotifier<TodayViewState> {
  @override
  Future<TodayViewState> build() {
    return ref.read(todayRepositoryProvider).fetchToday();
  }

  /// Re-runs the fetch, surfaced to the UI as pull-to-refresh (UX/UI
  /// Design Bible Section 15: "Used on list/feed-style screens (Today,
  /// history, coach)") and as the page-level error state's retry action.
  Future<void> refresh() async {
    state = const AsyncValue<TodayViewState>.loading();
    state = await AsyncValue.guard(
      () => ref.read(todayRepositoryProvider).fetchToday(),
    );
  }
}

final AsyncNotifierProvider<TodayController, TodayViewState>
    todayControllerProvider =
    AsyncNotifierProvider<TodayController, TodayViewState>(
  TodayController.new,
);
