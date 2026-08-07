import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../features/coach/presentation/coach_screen.dart';
import '../features/fuel/presentation/food_search_screen.dart';
import '../features/fuel/presentation/fuel_home_screen.dart';
import '../features/fuel/presentation/log_meal_screen.dart';
import '../features/fuel/presentation/supplements_screen.dart';
import '../features/progress/presentation/progress_screen.dart';
import '../features/today/presentation/today_screen.dart';
import '../features/train/presentation/active_workout_screen.dart';
import '../features/train/presentation/exercise_detail_screen.dart';
import '../features/train/presentation/personal_records_screen.dart';
import '../features/train/presentation/pre_session_screen.dart';
import '../features/train/presentation/session_summary_screen.dart';
import '../features/train/presentation/train_home_screen.dart';
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
              builder: (context, state) => const TrainHomeScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/fuel',
              builder: (context, state) => const FuelHomeScreen(),
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

    // ## Train's sub-screens: top-level routes, not nested branch routes
    //
    // `StatefulShellRoute.indexedStack` keeps `AppShell`'s single
    // `Scaffold` — global top bar and bottom `NavigationBar` included —
    // mounted for every route pushed onto a branch's own nested
    // `Navigator`. That is exactly right for `/train` itself (a tab
    // root), but wrong for a genuine full-screen drill-in: Active
    // Workout logging sessions with the five-tab bar still visible and
    // tappable underneath would risk a stray tap ending the workout flow
    // by accident, and none of Pre-session/Active Workout/Summary/
    // Exercise Detail/Records read as "still inside the Train tab" the
    // way Today's own FAB sheet does — each is its own full-screen
    // moment with its own back arrow, per the UX/UI Design Bible's own
    // per-screen Entry/Exit points. `parentNavigatorKey: _rootNavigatorKey`
    // pushes each of these onto the *root* Navigator, above the entire
    // `AppShell`, exactly like a typical "detail screen pushed from a
    // tab" pattern — each screen below builds its own `Scaffold`/`AppBar`
    // accordingly. See `docs/adr/0037-train-module.md`.
    GoRoute(
      path: '/train/pre-session/:workoutId',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => PreSessionScreen(
        workoutId: state.pathParameters['workoutId']!,
      ),
    ),
    GoRoute(
      path: '/train/session/:sessionId',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => ActiveWorkoutScreen(
        sessionId: state.pathParameters['sessionId']!,
      ),
    ),
    GoRoute(
      path: '/train/session/:sessionId/summary',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => SessionSummaryScreen(
        sessionId: state.pathParameters['sessionId']!,
        // `extra` carries a plain `bool`: `true` when reached via
        // `pushReplacement` straight off Active Workout ending
        // (`ActiveWorkoutScreen._endSession`), `false`/absent when
        // reached by tapping a past session in Train Home's History tab
        // (`TrainHistoryTile`, which pushes with no `extra` at all) —
        // see `SessionSummaryScreen`'s own doc comment for why this one
        // flag is the only thing that differs between the two cases.
        cameFromActiveSession: state.extra as bool? ?? false,
      ),
    ),
    GoRoute(
      path: '/train/exercise/:exerciseId',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => ExerciseDetailScreen(
        exerciseId: state.pathParameters['exerciseId']!,
        exerciseName: state.extra as String?,
      ),
    ),
    GoRoute(
      path: '/train/records',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const PersonalRecordsScreen(),
    ),

    // ## Fuel's sub-screens: the same root-navigator pattern as Train's
    //
    // See the comment above Train's routes for the full reasoning
    // (`docs/adr/0037-train-module.md`) — it applies unchanged here.
    // `docs/adr/0038-fuel-module.md` covers Fuel's own decisions.
    GoRoute(
      path: '/fuel/log-meal',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const LogMealScreen(),
    ),
    GoRoute(
      path: '/fuel/search',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const FoodSearchScreen(),
    ),
    GoRoute(
      path: '/fuel/supplements',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const SupplementsScreen(),
    ),
  ],
);
