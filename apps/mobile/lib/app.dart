import 'package:flutter/material.dart';

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
class GymCompanionApp extends StatelessWidget {
  const GymCompanionApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Gym Companion',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: ThemeMode.system,
      routerConfig: appRouter,
    );
  }
}
