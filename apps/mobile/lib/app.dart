import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'design/theme/app_theme.dart';
import 'shell/app_router.dart';

/// Root widget. Kept deliberately thin, matching the backend's `app/main.py`
/// factory — this file wires things together and holds no feature logic.
///
/// `theme`/`darkTheme` come from `AppTheme` (`lib/design/theme/app_theme.dart`)
/// — the hand-built design system, not a `colorSchemeSeed` shortcut (see that
/// file's own doc comment for why). `themeMode: ThemeMode.system` follows the
/// OS light/dark setting rather than forcing one mode: this app has no
/// in-product theme toggle yet, and defaulting to the platform's own choice
/// is the correct behavior until a Settings screen adds an explicit
/// override, not a placeholder to revisit.
///
/// A [ConsumerWidget], not [StatelessWidget], since
/// `docs/adr/0042-production-integration-plan.md` Step 2 — the real
/// authentication module — needs `routerProvider`
/// (`lib/shell/app_router.dart`) instead of the bare top-level
/// `appRouter` this file used before: the real auth guard only works
/// when the router itself is built with `ref` access. `ref.watch` here
/// only re-fetches the (stable, singleton) `GoRouter` instance if
/// `routerProvider` itself were ever invalidated — day to day, this
/// widget does not rebuild when auth state changes; the router's own
/// internal `refreshListenable` handles that without rebuilding
/// `MaterialApp.router`'s subtree.
class GymCompanionApp extends ConsumerWidget {
  const GymCompanionApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final GoRouter router = ref.watch(routerProvider);
    return MaterialApp.router(
      title: 'Gym Companion',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: ThemeMode.system,
      routerConfig: router,
    );
  }
}
