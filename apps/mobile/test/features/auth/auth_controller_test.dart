import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/core/network/api_exception.dart';
import 'package:gym_companion_mobile/features/auth/application/auth_controller.dart';
import 'package:gym_companion_mobile/features/auth/domain/auth_models.dart';

/// A controllable fake — real backend response shapes, no network I/O.
/// [failLogin]/[failRegister]/[failRefresh] each throw a real
/// [ApiException] shape rather than a generic [Exception], since
/// [AuthController]'s own error-mapping (`login_screen.dart`'s
/// `_messageFor`) branches on [ApiException]'s convenience getters.
class _FakeAuthRepository implements AuthRepository {
  _FakeAuthRepository({
    this.failLogin = false,
    this.failRegister = false,
    this.failRefresh = false,
  });

  bool failLogin;
  bool failRegister;
  bool failRefresh;
  int refreshCallCount = 0;
  int logoutCallCount = 0;

  static const AuthTokens tokens = AuthTokens(
    accessToken: 'access-1',
    refreshToken: 'refresh-1',
    tokenType: 'bearer',
    expiresIn: 900,
  );

  static final AuthUser user = AuthUser(
    userId: 'u1',
    email: 'a@b.com',
    role: AuthRole.member,
    accountStatus: AccountStatus.active,
    locale: 'en-US',
    timezone: 'UTC',
    createdAt: DateTime.utc(2026, 1, 1),
  );

  @override
  Future<AuthTokens> login({required String email, required String password}) async {
    if (failLogin) {
      throw const ApiException(statusCode: 401, message: 'incorrect');
    }
    return tokens;
  }

  @override
  Future<AuthTokens> register({
    required String email,
    required String password,
    required String locale,
    required String timezone,
  }) async {
    if (failRegister) {
      throw const ApiException(statusCode: 400, message: 'email already registered');
    }
    return tokens;
  }

  @override
  Future<AuthTokens> refresh({required String refreshToken}) async {
    refreshCallCount++;
    if (failRefresh) {
      throw const ApiException(statusCode: 401, message: 'refresh token expired');
    }
    return tokens;
  }

  @override
  Future<void> logout() async {
    logoutCallCount++;
  }

  @override
  Future<AuthUser> currentUser() async => user;
}

class _FakeTokenStorage implements TokenStorage {
  _FakeTokenStorage({String? seed}) : _stored = seed;

  String? _stored;

  @override
  Future<void> saveTokens(AuthTokens tokens) async {
    _stored = tokens.refreshToken;
  }

  @override
  Future<String?> readRefreshToken() async => _stored;

  @override
  Future<void> clear() async {
    _stored = null;
  }
}

ProviderContainer _container({
  required AuthRepository repository,
  required TokenStorage storage,
}) {
  final ProviderContainer container = ProviderContainer(
    overrides: <Override>[
      authRepositoryProvider.overrideWithValue(repository),
      tokenStorageProvider.overrideWithValue(storage),
    ],
  );
  addTearDown(container.dispose);
  return container;
}

void main() {
  group('AuthController.build (cold start)', () {
    test('no stored refresh token resolves straight to AuthUnauthenticated', () async {
      final ProviderContainer container = _container(
        repository: _FakeAuthRepository(),
        storage: _FakeTokenStorage(),
      );

      final AuthState state = await container.read(authControllerProvider.future);

      expect(state, isA<AuthUnauthenticated>());
    });

    test('a valid stored refresh token resolves to AuthAuthenticated with the real user', () async {
      final ProviderContainer container = _container(
        repository: _FakeAuthRepository(),
        storage: _FakeTokenStorage(seed: 'refresh-1'),
      );

      final AuthState state = await container.read(authControllerProvider.future);

      expect(state, isA<AuthAuthenticated>());
      expect((state as AuthAuthenticated).user.email, 'a@b.com');
      expect(
        container.read(authControllerProvider.notifier).currentAccessToken,
        'access-1',
      );
    });

    test('a stored refresh token that the backend rejects clears storage and resolves '
        'to AuthUnauthenticated, not a stuck error state', () async {
      final _FakeTokenStorage storage = _FakeTokenStorage(seed: 'stale-token');
      final ProviderContainer container = _container(
        repository: _FakeAuthRepository(failRefresh: true),
        storage: storage,
      );

      final AuthState state = await container.read(authControllerProvider.future);

      expect(state, isA<AuthUnauthenticated>());
      expect(await storage.readRefreshToken(), isNull);
    });
  });

  group('AuthController.login/register', () {
    test('a successful login moves state to AuthAuthenticated and persists the refresh token',
        () async {
      final _FakeTokenStorage storage = _FakeTokenStorage();
      final ProviderContainer container = _container(
        repository: _FakeAuthRepository(),
        storage: storage,
      );
      await container.read(authControllerProvider.future); // settle cold start

      await container.read(authControllerProvider.notifier).login(
            email: 'a@b.com',
            password: 'secret',
          );

      expect(container.read(authControllerProvider).value, isA<AuthAuthenticated>());
      expect(await storage.readRefreshToken(), 'refresh-1');
    });

    test('a failed login (real 401) surfaces as an AsyncError, not a silent no-op', () async {
      final ProviderContainer container = _container(
        repository: _FakeAuthRepository(failLogin: true),
        storage: _FakeTokenStorage(),
      );
      await container.read(authControllerProvider.future);

      await container.read(authControllerProvider.notifier).login(
            email: 'a@b.com',
            password: 'wrong',
          );

      final AsyncValue<AuthState> state = container.read(authControllerProvider);
      expect(state.hasError, isTrue);
      expect((state.error as ApiException).isUnauthorized, isTrue);
    });

    test('a successful registration moves state to AuthAuthenticated', () async {
      final ProviderContainer container = _container(
        repository: _FakeAuthRepository(),
        storage: _FakeTokenStorage(),
      );
      await container.read(authControllerProvider.future);

      await container.read(authControllerProvider.notifier).register(
            email: 'new@b.com',
            password: 'secret',
            locale: 'en-US',
            timezone: 'UTC',
          );

      expect(container.read(authControllerProvider).value, isA<AuthAuthenticated>());
    });
  });

  group('AuthController.logout', () {
    test('calls the real backend logout endpoint and clears local state', () async {
      final _FakeAuthRepository repo = _FakeAuthRepository();
      final _FakeTokenStorage storage = _FakeTokenStorage(seed: 'refresh-1');
      final ProviderContainer container = _container(repository: repo, storage: storage);
      await container.read(authControllerProvider.future);

      await container.read(authControllerProvider.notifier).logout();

      expect(repo.logoutCallCount, 1);
      expect(container.read(authControllerProvider).value, isA<AuthUnauthenticated>());
      expect(await storage.readRefreshToken(), isNull);
      expect(container.read(authControllerProvider.notifier).currentAccessToken, isNull);
    });
  });

  group('AuthController.attemptRefresh (the closure AuthInterceptor calls)', () {
    test('returns true and updates the in-memory access token on success', () async {
      final ProviderContainer container = _container(
        repository: _FakeAuthRepository(),
        storage: _FakeTokenStorage(seed: 'refresh-1'),
      );
      await container.read(authControllerProvider.future);

      final bool ok = await container.read(authControllerProvider.notifier).attemptRefresh();

      expect(ok, isTrue);
      expect(
        container.read(authControllerProvider.notifier).currentAccessToken,
        'access-1',
      );
    });

    test('returns false, never throws, when the backend rejects the refresh token', () async {
      final ProviderContainer container = _container(
        repository: _FakeAuthRepository(failRefresh: true),
        storage: _FakeTokenStorage(seed: 'refresh-1'),
      );
      await container.read(authControllerProvider.future);

      final bool ok = await container.read(authControllerProvider.notifier).attemptRefresh();

      expect(ok, isFalse);
    });

    test('returns false immediately when there is no stored refresh token at all', () async {
      final ProviderContainer container = _container(
        repository: _FakeAuthRepository(),
        storage: _FakeTokenStorage(),
      );
      await container.read(authControllerProvider.future);

      final bool ok = await container.read(authControllerProvider.notifier).attemptRefresh();

      expect(ok, isFalse);
    });
  });

  group('AuthController.forceLogoutFromRefreshFailure (the closure onRefreshFailed calls)', () {
    test('clears local state without calling the backend logout endpoint', () async {
      final _FakeAuthRepository repo = _FakeAuthRepository();
      final ProviderContainer container = _container(
        repository: repo,
        storage: _FakeTokenStorage(seed: 'refresh-1'),
      );
      await container.read(authControllerProvider.future);

      await container.read(authControllerProvider.notifier).forceLogoutFromRefreshFailure();

      expect(repo.logoutCallCount, 0);
      expect(container.read(authControllerProvider).value, isA<AuthUnauthenticated>());
    });
  });
}
