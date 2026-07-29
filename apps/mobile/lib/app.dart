import 'package:flutter/material.dart';

import 'shell/app_router.dart';

/// Root widget. Kept deliberately thin, matching the backend's `app/main.py`
/// factory — this file wires things together and holds no feature logic.
class GymCompanionApp extends StatelessWidget {
  const GymCompanionApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Gym Companion',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFF1F2937),
      ),
      routerConfig: appRouter,
    );
  }
}
