import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app.dart';
import 'features/fuel/application/fuel_controller.dart';
import 'features/fuel/infrastructure/mock_fuel_repository.dart';
import 'features/today/application/today_controller.dart';
import 'features/today/infrastructure/mock_today_repository.dart';
import 'features/train/application/train_controller.dart';
import 'features/train/infrastructure/mock_train_repository.dart';

/// The one place a provider's real implementation is chosen over its
/// default. [todayRepositoryProvider]/[trainRepositoryProvider]/
/// [fuelRepositoryProvider] have no default (they throw — see each one's
/// own doc comment) precisely so a real repository can't be forgotten
/// silently; their mock implementations are wired in here, honestly,
/// until authenticated API-backed repositories replace them. A widget
/// test overrides the same providers with its own fakes instead of this
/// file — none of `TodayController`/`TrainHomeController`/
/// `FuelHomeController`/etc. need to know which.
void main() {
  runApp(
    ProviderScope(
      overrides: <Override>[
        todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
        trainRepositoryProvider.overrideWithValue(MockTrainRepository()),
        fuelRepositoryProvider.overrideWithValue(MockFuelRepository()),
      ],
      child: const GymCompanionApp(),
    ),
  );
}
