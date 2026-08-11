import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../design/design.dart';
import '../features/auth/application/auth_controller.dart';
import '../features/today/presentation/widgets/quick_add_sheet.dart';

/// The persistent global top bar and five-tab bottom navigation, per the
/// UX/UI Design Bible Sections 3-4.
///
/// The Context chip, search, and notification bell remain placeholders —
/// they render but carry no behavior yet; see `docs/TECH_DEBT.md`'s
/// TD-0003 for the trigger conditions under which each should get a
/// real destination. Settings is the one exception: `docs/adr/0044-
/// authentication-module.md` (Step 2 of `docs/adr/0042-production-
/// integration-plan.md`) gives it the real, honest destination TD-0003
/// itself already named as its own trigger condition — "Settings has an
/// obvious real destination once any account/profile screen exists" —
/// specifically, real sign-out, not yet a full account/profile screen
/// (no such screen exists in this app; a real one is future scope, not
/// fabricated here). Settings is deliberately not a sixth tab (UX Bible
/// Section 3): it is reached from the avatar action here, from any tab.
///
/// All five tab icons now route through [AppIcons] rather than four of
/// them using a bare `Icons.*` literal — the other half of TD-0003,
/// closed here since this file is already being touched for the
/// Settings/logout wiring above; a mechanical fix with no behavior
/// change, exactly as TD-0003 itself anticipated.
///
/// ## The FAB lives here, not in `TodayScreen`
///
/// UX/UI Design Bible Section 4: "One FAB, scoped to the Today tab only."
/// `go_router`'s `StatefulShellRoute.indexedStack` gives each tab its own
/// navigation stack inside this shell's single `Scaffold` — there is only
/// one `Scaffold`, and Flutter's `floatingActionButton` slot belongs to
/// whichever `Scaffold` is nearest, so a per-tab FAB is necessarily this
/// file's concern, keyed off [navigationShell.currentIndex], not
/// something `TodayScreen` could own itself without nesting a second
/// `Scaffold` purely to get a FAB slot. [QuickAddSheet]'s *content* is
/// still Today-specific and lives under `features/today/`; this file
/// only decides *when the FAB appears*, never what quick-add actually
/// does.
class AppShell extends ConsumerWidget {
  const AppShell({required this.navigationShell, super.key});

  final StatefulNavigationShell navigationShell;

  static const _destinations = <NavigationDestination>[
    NavigationDestination(icon: Icon(AppIcons.today), selectedIcon: Icon(AppIcons.todaySelected), label: 'Today'),
    NavigationDestination(icon: Icon(AppIcons.train), selectedIcon: Icon(AppIcons.trainSelected), label: 'Train'),
    NavigationDestination(icon: Icon(AppIcons.fuel), selectedIcon: Icon(AppIcons.fuelSelected), label: 'Fuel'),
    NavigationDestination(icon: Icon(AppIcons.progress), selectedIcon: Icon(AppIcons.progressSelected), label: 'Progress'),
    NavigationDestination(
      icon: Icon(AppIcons.coach),
      selectedIcon: Icon(AppIcons.coachSelected),
      label: 'Coach',
    ),
  ];

  Future<void> _confirmLogout(BuildContext context, WidgetRef ref) async {
    final bool? confirmed = await showAppConfirmationDialog(
      context: context,
      title: 'Log out?',
      message: "You'll need to sign in again to continue.",
      confirmLabel: 'Log out',
      isDestructive: false,
    );
    if (confirmed == true) {
      await ref.read(authControllerProvider.notifier).logout();
      // No explicit navigation here — logout moves authControllerProvider
      // to AuthUnauthenticated, which the router's own reactive redirect
      // (lib/shell/app_router.dart) already sends to /login on its own,
      // the same pattern Login/Register's own onPressed handlers use.
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(
        leading: Padding(
          padding: const EdgeInsets.all(AppSpacing.sm),
          child: Chip(
            label: const Text('Home'),
            avatar: const Icon(AppIcons.location, size: 18),
            onDeleted: null,
          ),
        ),
        leadingWidth: 120,
        title: const SizedBox.shrink(),
        actions: [
          IconButton(
            tooltip: 'Search',
            icon: const Icon(AppIcons.search),
            onPressed: () {},
          ),
          IconButton(
            tooltip: 'Notifications',
            icon: const Icon(AppIcons.notifications),
            onPressed: () {},
          ),
          IconButton(
            tooltip: 'Log out',
            icon: const Icon(AppIcons.settings),
            onPressed: () => _confirmLogout(context, ref),
          ),
        ],
      ),
      body: navigationShell,
      floatingActionButton: navigationShell.currentIndex == 0
          ? FloatingActionButton(
              tooltip: 'Quick add',
              onPressed: () => showAppBottomSheet(
                context: context,
                builder: (BuildContext context) => const QuickAddSheet(),
              ),
              child: const Icon(AppIcons.add),
            )
          : null,
      bottomNavigationBar: NavigationBar(
        selectedIndex: navigationShell.currentIndex,
        onDestinationSelected: (index) {
          // Tapping the already-active tab returns its stack to the top,
          // per UX/UI Design Bible Section 4 — go_router does this
          // automatically when initialLocation is used for the branch.
          navigationShell.goBranch(
            index,
            initialLocation: index == navigationShell.currentIndex,
          );
        },
        destinations: _destinations,
      ),
    );
  }
}
