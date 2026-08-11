import '../application/auth_controller.dart';
import '../domain/auth_models.dart';

/// A disclosed test-only double — **never wired in `lib/main.dart`**,
/// unlike every other feature's `MockXRepository`. `ApiAuthRepository`'s
/// own doc comment explains why Auth never had a "mock until the real
/// backend arrives" era to begin with: the real backend already existed
/// when this module was built.
///
/// This exists purely so widget tests can boot the full app
/// (`GymCompanionApp`) without a real network call — every one of this
/// codebase's pre-existing feature tests now needs an auth-state
/// override for exactly the same structural reason Coach's own
/// `coachRepositoryProvider` override became mandatory in every test
/// (ADR 0041): `GoRouter`'s new auth guard (`lib/shell/app_router.dart`)
/// evaluates on the very first frame, so an unauthenticated default
/// would redirect every existing test straight to `/login` instead of
/// the screen it means to exercise. Paired with a seeded
/// `MockTokenStorage` (see that class below), the combination resolves
/// to [AuthAuthenticated] immediately — see `test/support/
/// auth_test_overrides.dart` for the one shared helper every test file
/// uses rather than repeating this pair of overrides by hand.
class MockAuthRepository implements AuthRepository {
  const MockAuthRepository();

  static final AuthUser mockUser = AuthUser(
    userId: 'mock-user-1',
    email: 'member@example.com',
    role: AuthRole.member,
    accountStatus: AccountStatus.active,
    locale: 'en-US',
    timezone: 'UTC',
    createdAt: DateTime.utc(2026, 1, 1),
  );

  static const String mockRefreshToken = 'mock-refresh-token';

  static const AuthTokens mockTokens = AuthTokens(
    accessToken: 'mock-access-token',
    refreshToken: mockRefreshToken,
    tokenType: 'bearer',
    expiresIn: 900,
  );

  @override
  Future<AuthTokens> register({
    required String email,
    required String password,
    required String locale,
    required String timezone,
  }) async =>
      mockTokens;

  @override
  Future<AuthTokens> login({required String email, required String password}) async => mockTokens;

  @override
  Future<AuthTokens> refresh({required String refreshToken}) async => mockTokens;

  @override
  Future<void> logout() async {}

  @override
  Future<AuthUser> currentUser() async => mockUser;
}

/// An in-memory [TokenStorage] double. Seeded with
/// [MockAuthRepository.mockTokens]'s own refresh token by default —
/// booting a test with both overridden this way means
/// `AuthController.build()` finds a stored refresh token immediately,
/// calls the (mock) `refresh`/`currentUser`, and resolves to
/// [AuthAuthenticated] with no real I/O — exactly what every
/// pre-existing test needs. Pass `seedRefreshToken: null` for the one
/// test that specifically wants to start from [AuthUnauthenticated]
/// (the login-flow test itself).
class MockTokenStorage implements TokenStorage {
  MockTokenStorage({String? seedRefreshToken = MockAuthRepository.mockRefreshToken})
      : _refreshToken = seedRefreshToken;

  String? _refreshToken;

  @override
  Future<void> saveTokens(AuthTokens tokens) async {
    _refreshToken = tokens.refreshToken;
  }

  @override
  Future<String?> readRefreshToken() async => _refreshToken;

  @override
  Future<void> clear() async {
    _refreshToken = null;
  }
}
