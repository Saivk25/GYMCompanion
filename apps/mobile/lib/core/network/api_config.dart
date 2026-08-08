import 'package:flutter/foundation.dart';

/// Where and how every real HTTP request this app makes is sent — the
/// one place a base URL or timeout is a literal constant, so no
/// individual repository or client ever hardcodes either.
///
/// ## Why [baseUrl] is a getter, not a `const`
///
/// The backend's real dev deployment (`infra/docker-compose.yml`) binds
/// to `localhost:8000` on the host machine — correct for iOS Simulator,
/// desktop, and a browser, all of which share the host's network
/// namespace. Android's emulator does not: it runs inside its own
/// virtual network, where `localhost` resolves to the emulator itself,
/// not the host machine, so Android's own documented address for "the
/// host machine's `localhost`" is `10.0.2.2`
/// (https://developer.android.com/studio/run/emulator-networking).
/// [defaultTargetPlatform] (not `dart:io`'s `Platform`, which does not
/// compile for a web target at all) is what lets this stay one pure-Dart
/// getter instead of a conditional-import split across two files.
///
/// A real per-environment override (staging/production base URLs) is
/// explicitly out of scope for this phase — see
/// `docs/adr/0042-production-integration-plan.md`, which named exactly
/// this as a real, disclosed decision point for whenever this app is
/// first built against a non-local backend, not something to guess at
/// speculatively here.
abstract final class ApiConfig {
  static String get baseUrl {
    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000';
    }
    return 'http://localhost:8000';
  }

  /// Root-level, unprefixed — matches `backend/app/api/routes/auth.py`'s
  /// own placement (`POST /register`, not `POST /api/v1/register`).
  static const String authPathPrefix = '';

  /// Every other route in this API is mounted under this prefix
  /// (`backend/app/main.py`'s `app.include_router(..., prefix="/api/v1")`).
  static const String v1PathPrefix = '/api/v1';

  static const Duration connectTimeout = Duration(seconds: 10);
  static const Duration receiveTimeout = Duration(seconds: 15);
  static const Duration sendTimeout = Duration(seconds: 15);

  /// Applies only to idempotent (GET) requests that fail for a network-
  /// level reason — see [RetryInterceptor]'s own doc comment for why a
  /// mutation is never retried automatically.
  static const int maxRetries = 2;
}
