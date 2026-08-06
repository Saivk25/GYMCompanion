import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app.dart';
import 'features/today/application/today_controller.dart';
import 'features/today/infrastructure/mock_today_repository.dart';

/// The one place a provider's real implementation is chosen over its
/// default. [todayRepositoryProvider] has no default (it throws — see
/// its own doc comment) precisely so a real repository can't be
/// forgotten silently; [MockTodayRepository] is wired in here, honestly,
/// until an authenticated API-backed repository replaces it. A widget
/// test overrides the same provider with its own fake instead of this
/// one — neither `TodayController` nor `TodayScreen` need to know which.
void main() {
  runApp(
    ProviderScope(
      overrides: <Override>[
        todayRepositoryProvider.overrideWithValue(const MockTodayRepository()),
      ],
      child: const GymCompanionApp(),
    ),
  );
}
