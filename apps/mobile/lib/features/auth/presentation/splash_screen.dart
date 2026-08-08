import 'package:flutter/material.dart';

/// Shown for the brief window while `AuthController.build()` is
/// validating a stored refresh token on cold start — genuinely brief in
/// the common case (one `/refresh` + one `/me` call), but real: without
/// this screen, `/today`'s own content would render for a moment before
/// a redirect to `/login` could interrupt it, which both flashes real
/// UI a signed-out visitor should never see and makes an unnecessary
/// network call against `TodayRepository` before the auth guard has
/// even decided this session is real.
///
/// Deliberately minimal — a centered spinner, no logo animation or
/// splash art — matching this app's own calm, non-flashy design
/// philosophy (UX/UI Design Bible Section 11) applied to the one screen
/// most tempting to over-decorate.
class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(child: CircularProgressIndicator()),
    );
  }
}
