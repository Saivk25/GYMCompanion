import 'package:flutter/material.dart';

import '../design/design.dart';
import '../features/today/presentation/widgets/quick_add_sheet.dart';

/// The persistent global top bar and five-tab bottom navigation, per the
/// UX/UI Design Bible Sections 3-4.
///
/// The Context chip, search, and notification bell are placeholders in this
/// scaffolding sprint — they render but carry no behavior yet, matching how
/// the backend's `/health` endpoint proves the shell boots without yet
/// implementing a feature. Settings is deliberately not a sixth tab (UX
/// Bible Section 3): it is reached from the avatar action here, from any tab.
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
class AppShell extends StatelessWidget {
  const AppShell({required this.navigationShell, super.key});

  final StatefulNavigationShell navigationShell;

  static const _destinations = <NavigationDestination>[
    NavigationDestination(icon: Icon(Icons.today_outlined), selectedIcon: Icon(Icons.today), label: 'Today'),
    NavigationDestination(icon: Icon(Icons.fitness_center_outlined), selectedIcon: Icon(Icons.fitness_center), label: 'Train'),
    NavigationDestination(icon: Icon(Icons.restaurant_outlined), selectedIcon: Icon(Icons.restaurant), label: 'Fuel'),
    NavigationDestination(icon: Icon(Icons.show_chart_outlined), selectedIcon: Icon(Icons.show_chart), label: 'Progress'),
    NavigationDestination(icon: Icon(Icons.chat_bubble_outline), selectedIcon: Icon(Icons.chat_bubble), label: 'Coach'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: Padding(
          padding: const EdgeInsets.all(8.0),
          child: Chip(
            label: const Text('Home'),
            avatar: const Icon(Icons.place_outlined, size: 18),
            onDeleted: null,
          ),
        ),
        leadingWidth: 120,
        title: const SizedBox.shrink(),
        actions: [
          IconButton(
            tooltip: 'Search',
            icon: const Icon(Icons.search),
            onPressed: () {},
          ),
          IconButton(
            tooltip: 'Notifications',
            icon: const Icon(Icons.notifications_outlined),
            onPressed: () {},
          ),
          IconButton(
            tooltip: 'Settings',
            icon: const Icon(Icons.account_circle_outlined),
            onPressed: () {},
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
