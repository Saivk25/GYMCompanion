import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../features/coach/presentation/coach_history_screen.dart';
import '../features/coach/presentation/coach_home_screen.dart';
import '../features/coach/presentation/coach_signal_detail_screen.dart';
import '../features/coach/presentation/coach_weekly_review_screen.dart';
import '../features/fuel/presentation/food_search_screen.dart';
import '../features/fuel/presentation/fuel_home_screen.dart';
import '../features/fuel/presentation/log_meal_screen.dart';
import '../features/fuel/presentation/supplements_screen.dart';
import '../features/progress/domain/progress_models.dart';
import '../features/progress/presentation/insights_screen.dart';
import '../features/progress/presentation/log_measurement_screen.dart';
import '../features/progress/presentation/measurement_trend_screen.dart';
import '../features/progress/presentation/photo_checkin_screen.dart';
import '../features/progress/presentation/photo_comparison_screen.dart';
import '../features/progress/presentation/progress_home_screen.dart';
import '../features/readiness/presentation/readiness_checkin_screen.dart';
import '../features/readiness/presentation/readiness_entry_detail_screen.dart';
import '../features/readiness/presentation/readiness_formula_screen.dart';
import '../features/readiness/presentation/readiness_home_screen.dart';
import '../features/readiness/presentation/readiness_timeline_screen.dart';
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
              builder: (context, state) => const ProgressHomeScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/coach',
              builder: (context, state) => const CoachHomeScreen(),
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

    // ## Progress's sub-screens: the same root-navigator pattern as
    // Train's and Fuel's
    //
    // See the comment above Train's routes for the full reasoning
    // (`docs/adr/0037-train-module.md`) — it applies unchanged here.
    // `docs/adr/0039-progress-module.md` covers Progress's own decisions,
    // including why Photo Check-in, Photo Comparison, and Correlations
    // are real, reachable routes rather than omitted segments.
    GoRoute(
      path: '/progress/log-measurement',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const LogMeasurementScreen(),
    ),
    GoRoute(
      path: '/progress/measurement/:metric',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => MeasurementTrendScreen(
        metric: MeasurementMetric.values.byName(state.pathParameters['metric']!),
      ),
    ),
    GoRoute(
      path: '/progress/photo-checkin',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const PhotoCheckinScreen(),
    ),
    GoRoute(
      path: '/progress/photo-comparison',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const PhotoComparisonScreen(),
    ),
    GoRoute(
      path: '/progress/insights',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const InsightsScreen(),
    ),

    // ## Readiness: root-navigator routes, but with no tab of its own
    //
    // Readiness has never been one of the five bottom tabs (UX/UI Design
    // Bible Section 3) — unlike Train/Fuel/Progress, `/readiness` itself
    // is a root-navigator push, not a `StatefulShellBranch` route. It is
    // reached from Today's check-in nudge
    // (`ReadinessCheckInCard.onStart`) and from Progress's Recovery
    // segment, the same full-screen-drill-in pattern Train's and Fuel's
    // own sub-screens already established — see the comment above
    // Train's routes for the full reasoning. `docs/adr/0040-readiness-
    // module.md` covers Readiness's own decisions.
    GoRoute(
      path: '/readiness',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const ReadinessHomeScreen(),
    ),
    GoRoute(
      path: '/readiness/check-in',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const ReadinessCheckInScreen(),
    ),
    GoRoute(
      path: '/readiness/timeline',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const ReadinessTimelineScreen(),
    ),
    GoRoute(
      path: '/readiness/entry/:readinessId',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => ReadinessEntryDetailScreen(
        readinessId: state.pathParameters['readinessId']!,
      ),
    ),
    GoRoute(
      path: '/readiness/formula',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const ReadinessFormulaScreen(),
    ),

    // ## Coach's sub-screens: the same root-navigator pattern as every
    // other module's drill-ins
    //
    // Unlike Readiness, `/coach` itself *is* one of the five tabs (it
    // always has been — see the `StatefulShellBranch` above) — only its
    // own drill-ins (one signal's detail, Weekly Review, Coaching
    // History) are root-navigator pushes, the same full-screen-drill-in
    // pattern every other module's own sub-screens already established;
    // see the comment above Train's routes for the full reasoning.
    // `docs/adr/0041-coach-module.md` covers Coach's own decisions.
    GoRoute(
      path: '/coach/signal/:signalId',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => CoachSignalDetailScreen(
        signalId: state.pathParameters['signalId']!,
      ),
    ),
    GoRoute(
      path: '/coach/weekly-review',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const CoachWeeklyReviewScreen(),
    ),
    GoRoute(
      path: '/coach/history',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const CoachHistoryScreen(),
    ),
  ],
);
