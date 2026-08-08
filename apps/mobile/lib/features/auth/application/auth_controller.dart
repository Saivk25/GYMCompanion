import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/auth_models.dart';

/// The seam between Auth's presentation layer and wherever session
/// data actually comes from — mirrors every other feature's own
/// `XRepository` interface pattern (`TodayRepository`,
/// `ReadinessRepository`, ...), applied to the one module in this app
/// whose real implementation (`ApiAuthRepository`,
/// `../infrastructure/api_auth_repository.dart`) is built in the same
/// phase as its interface, rather than following a mock built first —
/// see that file's own doc comment for why Auth does not get the
/// "mock until a real backend arrives" treatment every earlier module
/// did: the real backend already exists and this phase's entire job is
/// wiring it, so a mock here would be built and discarded in the same
/// commit.
abstract interface class AuthRepository {
  Future<AuthTokens> register({
    required String email,
    required String password,
    required String locale,
    required String timezone,
  });

  Future<AuthTokens> login({required String email, required String password});

  Future<AuthTokens> refresh({required String refreshToken});

  /// Revokes the refresh token server-side
  /// (`backend/app/api/routes/auth.py`'s `POST /logout`) — a real
  /// network call, not merely a local state clear.
  Future<void> logout();

  Future<AuthUser> currentUser();
}

/// Persists exactly one secret across app restarts: the refresh token.
/// The access token is never written here — see [AuthController.
/// currentAccessToken]'s own doc comment for why that is a deliberate
/// choice, not an oversight.
abstract interface class TokenStorage {
  Future<void> saveTokens(AuthTokens tokens);
  Future<String?> readRefreshToken();
  Future<void> clear();
}

final Provider<AuthRepository> authRepositoryProvider = Provider<AuthRepository>(
  (ref) => throw UnimplementedError(
    'authRepositoryProvider has no default implementation — see lib/main.dart, '
    'which overrides it with ApiAuthRepository.',
  ),
);

final Provider<TokenStorage> tokenStorageProvider = Provider<TokenStorage>(
  (ref) => throw UnimplementedError(
    'tokenStorageProvider has no default implementation — see lib/main.dart, '
    'which overrides it with SecureTokenStorage.',
  ),
);

/// The single source of truth for "is anyone signed in, and who."
/// `GoRouter`'s auth guard (`lib/shell/app_router.dart`'s `redirect`)
/// watches this provider directly; every screen that needs to show a
/// signed-in user's identity reads it the same way any other feature's
/// `XHomeController` is read.
///
/// [AuthState]'s own three-way split (`AuthInitial`/`AuthAuthenticated`/
/// `AuthUnauthenticated`) is deliberately not collapsed into a bare
/// `AuthUser?` — see that type's own doc comment. [AsyncNotifier]'s own
/// `loading`/`error`/`data` states layer on top of that: `loading`
/// covers the brief window while [build] is validating a stored refresh
/// token on cold start (functionally the same moment [AuthInitial]
/// describes, from the router guard's point of view — both mean "don't
/// redirect yet").
class AuthController extends AsyncNotifier<AuthState> {
  String? _accessToken;

  /// Read by `lib/main.dart`'s `apiClientProvider` — the plain,
  /// synchronous-to-call closure `AuthInterceptor` needs on every
  /// outgoing request, rather than making every request await this
  /// provider's own `AsyncValue<AuthState>`.
  ///
  /// Deliberately **not** persisted anywhere — [TokenStorage] only ever
  /// writes the refresh token. The access token's own short TTL
  /// (`backend/app/core/config.py`: 15 minutes) means persisting it
  /// would save, at most, 15 minutes of "skip one network call after a
  /// cold start," at the real cost of a second secret written to disk;
  /// [build] already re-derives a fresh one from the (securely stored)
  /// refresh token on every app launch.
  String? get currentAccessToken => _accessToken;

  @override
  Future<AuthState> build() async {
    final String? storedRefreshToken = await ref.read(tokenStorageProvider).readRefreshToken();
    if (storedRefreshToken == null) {
      return const AuthUnauthenticated();
    }
    try {
      final AuthTokens tokens =
          await ref.read(authRepositoryProvider).refresh(refreshToken: storedRefreshToken);
      _accessToken = tokens.accessToken;
      await ref.read(tokenStorageProvider).saveTokens(tokens);
      final AuthUser user = await ref.read(authRepositoryProvider).currentUser();
      return AuthAuthenticated(user);
    } on Object {
      // A stored refresh token that no longer works (expired, revoked,
      // or the backend rejected it for any reason) means this device is
      // not actually signed in — clear it rather than retry forever on
      // every cold start.
      _accessToken = null;
      await ref.read(tokenStorageProvider).clear();
      return const AuthUnauthenticated();
    }
  }

  Future<void> login({required String email, required String password}) async {
    state = const AsyncValue<AuthState>.loading();
    state = await AsyncValue.guard(() async {
      final AuthTokens tokens =
          await ref.read(authRepositoryProvider).login(email: email, password: password);
      return _commitSession(tokens);
    });
  }

  Future<void> register({
    required String email,
    required String password,
    required String locale,
    required String timezone,
  }) async {
    state = const AsyncValue<AuthState>.loading();
    state = await AsyncValue.guard(() async {
      final AuthTokens tokens = await ref.read(authRepositoryProvider).register(
            email: email,
            password: password,
            locale: locale,
            timezone: timezone,
          );
      return _commitSession(tokens);
    });
  }

  /// Real logout: calls the backend's own revocation endpoint before
  /// clearing local state. A failed server call (e.g. offline) never
  /// traps the user in a signed-in-looking state on their own device —
  /// local state is always cleared regardless of whether the network
  /// call succeeded.
  Future<void> logout() async {
    try {
      await ref.read(authRepositoryProvider).logout();
    } on Object {
      // Deliberately swallowed — see the doc comment above.
    }
    await _clearLocalSession();
  }

  /// Called only by `apiClientProvider`'s `onRefreshFailed` callback
  /// (`lib/main.dart`) — `AuthInterceptor` already attempted and lost a
  /// refresh, so there is no further server call worth making here;
  /// this only clears local state so the router guard redirects to
  /// Login on the next frame.
  Future<void> forceLogoutFromRefreshFailure() => _clearLocalSession();

  /// Called only by `apiClientProvider`'s `refreshToken` closure — the
  /// one path a background 401 takes to obtain a new access token
  /// without the user doing anything. Returns `false` (never throws) on
  /// any failure, letting `AuthInterceptor` decide what happens next.
  Future<bool> attemptRefresh() async {
    final String? storedRefreshToken = await ref.read(tokenStorageProvider).readRefreshToken();
    if (storedRefreshToken == null) {
      return false;
    }
    try {
      final AuthTokens tokens =
          await ref.read(authRepositoryProvider).refresh(refreshToken: storedRefreshToken);
      _accessToken = tokens.accessToken;
      await ref.read(tokenStorageProvider).saveTokens(tokens);
      return true;
    } on Object {
      return false;
    }
  }

  Future<AuthState> _commitSession(AuthTokens tokens) async {
    _accessToken = tokens.accessToken;
    await ref.read(tokenStorageProvider).saveTokens(tokens);
    final AuthUser user = await ref.read(authRepositoryProvider).currentUser();
    return AuthAuthenticated(user);
  }

  Future<void> _clearLocalSession() async {
    _accessToken = null;
    await ref.read(tokenStorageProvider).clear();
    state = const AsyncValue<AuthState>.data(AuthUnauthenticated());
  }
}

final AsyncNotifierProvider<AuthController, AuthState> authControllerProvider =
    AsyncNotifierProvider<AuthController, AuthState>(AuthController.new);
