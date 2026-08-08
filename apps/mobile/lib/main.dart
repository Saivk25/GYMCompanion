import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app.dart';
import 'core/network/network.dart';
import 'features/auth/application/auth_controller.dart';
import 'features/auth/infrastructure/api_auth_repository.dart';
import 'features/auth/infrastructure/secure_token_storage.dart';
import 'features/coach/application/coach_controller.dart';
import 'features/coach/infrastructure/mock_coach_repository.dart';
import 'features/fuel/application/fuel_controller.dart';
import 'features/fuel/infrastructure/mock_fuel_repository.dart';
import 'features/progress/application/progress_controller.dart';
import 'features/progress/infrastructure/mock_progress_repository.dart';
import 'features/readiness/application/readiness_controller.dart';
import 'features/readiness/infrastructure/api_readiness_repository.dart';
import 'features/today/application/today_controller.dart';
import 'features/today/infrastructure/api_today_repository.dart';
import 'features/train/application/train_controller.dart';
import 'features/train/infrastructure/mock_train_repository.dart';
import 'shared/application/coach_signal_log.dart';

/// The single shared [ApiClient] every real (`ApiX`-prefixed)
/// repository will use — one `Dio` instance, one interceptor chain, for
/// the whole app, rather than a client per feature. Defined here, not
/// inside `lib/core/network/`, deliberately: `ApiClient` itself must
/// stay agnostic to what "a token" or "a refresh" means (see its own
/// doc comment — `lib/core/network/` has zero imports of
/// `lib/features/`), so the three closures wiring it to
/// [authControllerProvider] have to live at the one place that is
/// already allowed to depend on both — the composition root.
///
/// [ApiAuthRepository] itself is also built on this same client — its
/// own `login`/`register`/`refresh` calls pass `skipAuthHeader`/
/// `skipAuthRetry` (see that file) rather than needing a second,
/// auth-free client instance.
final Provider<ApiClient> apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(
    accessTokenProvider: () async => ref.read(authControllerProvider.notifier).currentAccessToken,
    refreshToken: () => ref.read(authControllerProvider.notifier).attemptRefresh(),
    onRefreshFailed: () => ref.read(authControllerProvider.notifier).forceLogoutFromRefreshFailure(),
  );
});

/// The one place a provider's real implementation is chosen over its
/// default. [trainRepositoryProvider]/[fuelRepositoryProvider]/
/// [progressRepositoryProvider]/[coachRepositoryProvider] have no
/// default (they throw — see each one's own doc comment) precisely so a
/// real repository can't be forgotten silently; their mock
/// implementations are wired in here, honestly, until authenticated
/// API-backed repositories replace them, one Step-3 feature at a time
/// (`docs/adr/0042`'s own Today/Readiness/Train/Fuel/Progress/Coach
/// order) — except [coachRepositoryProvider], see its own doc comment
/// for why "real API-backed" is never coming for that one specifically.
/// A widget test overrides the same providers with its own fakes
/// instead of this file — none of `TodayController`/
/// `TrainHomeController`/`FuelHomeController`/`ProgressHomeController`/
/// `ReadinessHomeController`/`CoachHomeController` need to know which.
///
/// [todayRepositoryProvider] and [readinessRepositoryProvider] have
/// already made that switch (`docs/adr/0046-today-repository-
/// integration.md`, `docs/adr/0047-readiness-repository-integration.md`)
/// — [ApiTodayRepository]/[ApiReadinessRepository] are wired here
/// instead of `MockTodayRepository`/[MockReadinessRepository] (both
/// still used by their own feature's widget tests, neither deleted).
/// Both use `overrideWith`, for the same reason [authRepositoryProvider]
/// below does: each needs a closure reading [apiClientProvider] at call
/// time, not a constant instance built before this `ProviderScope`
/// exists.
///
/// [coachRepositoryProvider] uses `overrideWith`, not `overrideWithValue`
/// like every other still-mocked provider here — [MockCoachRepository]
/// needs a closure reading [coachSignalLogProvider] at call time, not a
/// constant instance built before this `ProviderScope` even exists (see
/// `MockCoachRepository`'s own doc comment for why it has no state of
/// its own to construct with).
///
/// [authRepositoryProvider]/[tokenStorageProvider] are the pair wired to
/// their *real* implementations here — see `ApiAuthRepository`'s own doc
/// comment for why Auth has no "mock until the real backend arrives"
/// era the other four still-mocked providers went through.
void main() {
  runApp(
    ProviderScope(
      overrides: <Override>[
        todayRepositoryProvider.overrideWith(
          (ref) => ApiTodayRepository(ref.read(apiClientProvider)),
        ),
        trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
        fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
        progressRepositoryProvider.overrideWithValue(MockProgressRepository()),
        readinessRepositoryProvider.overrideWith(
          (ref) => ApiReadinessRepository(ref.read(apiClientProvider)),
        ),
        coachRepositoryProvider.overrideWith(
          (ref) => MockCoachRepository(() => ref.read(coachSignalLogProvider)),
        ),
        authRepositoryProvider.overrideWith(
          (ref) => ApiAuthRepository(ref.read(apiClientProvider)),
        ),
        tokenStorageProvider.overrideWithValue(SecureTokenStorage()),
      ],
      child: const GymCompanionApp(),
    ),
  );
}
