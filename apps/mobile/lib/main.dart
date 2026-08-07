import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app.dart';
import 'features/coach/application/coach_controller.dart';
import 'features/coach/infrastructure/mock_coach_repository.dart';
import 'features/fuel/application/fuel_controller.dart';
import 'features/fuel/infrastructure/mock_fuel_repository.dart';
import 'features/progress/application/progress_controller.dart';
import 'features/progress/infrastructure/mock_progress_repository.dart';
import 'features/readiness/application/readiness_controller.dart';
import 'features/readiness/infrastructure/mock_readiness_repository.dart';
import 'features/today/application/today_controller.dart';
import 'features/today/infrastructure/mock_today_repository.dart';
import 'features/train/application/train_controller.dart';
import 'features/train/infrastructure/mock_train_repository.dart';
import 'shared/application/coach_signal_log.dart';

/// The one place a provider's real implementation is chosen over its
/// default. [todayRepositoryProvider]/[trainRepositoryProvider]/
/// [fuelRepositoryProvider]/[progressRepositoryProvider]/
/// [readinessRepositoryProvider]/[coachRepositoryProvider] have no
/// default (they throw — see each one's own doc comment) precisely so a
/// real repository can't be forgotten silently; their mock
/// implementations are wired in here, honestly, until authenticated
/// API-backed repositories replace them (except [coachRepositoryProvider]
/// — see its own doc comment for why "real API-backed" is never coming
/// for that one specifically). A widget test overrides the same
/// providers with its own fakes instead of this file — none of
/// `TodayController`/`TrainHomeController`/`FuelHomeController`/
/// `ProgressHomeController`/`ReadinessHomeController`/`CoachHomeController`
/// need to know which.
///
/// [coachRepositoryProvider] uses `overrideWith`, not `overrideWithValue`
/// like every other provider here — [MockCoachRepository] needs a
/// closure reading [coachSignalLogProvider] at call time, not a
/// constant instance built before this `ProviderScope` even exists (see
/// `MockCoachRepository`'s own doc comment for why it has no state of
/// its own to construct with).
void main() {
  runApp(
    ProviderScope(
      overrides: <Override>[
        todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
        trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
        fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
        progressRepositoryProvider.overrideWithValue(MockProgressRepository()),
        readinessRepositoryProvider.overrideWithValue(MockReadinessRepository()),
        coachRepositoryProvider.overrideWith(
          (ref) => MockCoachRepository(() => ref.read(coachSignalLogProvider)),
        ),
      ],
      child: const GymCompanionApp(),
    ),
  );
}
