import 'package:flutter/material.dart';

/// The persistent global top bar and five-tab bottom navigation, per the
/// UX/UI Design Bible Sections 3-4.
///
/// The Context chip, search, and notification bell are placeholders in this
/// scaffolding sprint — they render but carry no behavior yet, matching how
/// the backend's `/health` endpoint proves the shell boots without yet
/// implementing a feature. Settings is deliberately not a sixth tab (UX
/// Bible Section 3): it is reached from the avatar action here, from any tab.
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
