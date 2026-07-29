import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../features/coach/presentation/coach_screen.dart';
import '../features/fuel/presentation/fuel_screen.dart';
import '../features/progress/presentation/progress_screen.dart';
import '../features/today/presentation/today_screen.dart';
import '../features/train/presentation/train_screen.dart';
import 'app_shell.dart';

/// The five bottom-tab destinations, in UX/UI Design Bible Section 3 order.
/// Today is first and is the default landing tab.
enum AppTab { today, train, fuel, progress, coach }

final GlobalKey<NavigatorState> _rootNavigatorKey = GlobalKey<NavigatorState>(
  debugLabel: 'root',
);

/// Each branch gets its own navigation stack (StatefulShellRoute), so
/// switching tabs never loses a tab's scroll/navigation position — this is
/// what the UX/UI Design Bible's Section 4 "nested navigation" rule assumes.
final GoRouter appRouter = GoRouter(
  navigatorKey: _rootNavigatorKey,
  initialLocation: '/today',
  routes: [
    StatefulShellRoute.indexedStack(
      builder: (context, state, navigationShell) {
        return AppShell(navigationShell: navigationShell);
      },
      branches: [
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/today',
              builder: (context, state) => const TodayScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/train',
              builder: (context, state) => const TrainScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/fuel',
              builder: (context, state) => const FuelScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/progress',
              builder: (context, state) => const ProgressScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/coach',
              builder: (context, state) => const CoachScreen(),
            ),
          ],
        ),
      ],
    ),
  ],
);
