import '../../../core/network/network.dart';
import '../application/auth_controller.dart';
import '../domain/auth_models.dart';

/// The real, and — unlike every other feature's `ApiXRepository` — the
/// *only* [AuthRepository] implementation this app has. Every other
/// module (`MockTodayRepository`, `MockTrainRepository`, ...) was built
/// as a disclosed placeholder before any real backend integration
/// existed; Auth is the first module built after that integration layer
/// (`lib/core/network/`, ADR 0043) already exists, so there was never a
/// "build the mock now, the real thing later" phase for it to go
/// through. `MockAuthRepository` (`mock_auth_repository.dart`) exists
/// only for widget tests that need to boot the app without a real
/// network call — see that file's own doc comment.
///
/// Every method here maps directly to one real endpoint documented in
/// `backend/app/api/routes/auth.py`'s own module docstring table — no
/// endpoint this app calls was invented or guessed at.
class ApiAuthRepository implements AuthRepository {
  ApiAuthRepository(this._client);

  final ApiClient _client;

  @override
  Future<AuthTokens> register({
    required String email,
    required String password,
    required String locale,
    required String timezone,
  }) async {
    final Map<String, dynamic> json = await _client.post(
      '/register',
      body: <String, dynamic>{
        'email': email,
        'password': password,
        'locale': locale,
        'timezone': timezone,
      },
      // No access token exists yet to attach, and a 401 here would be a
      // real "email already registered"-shaped failure (this endpoint
      // actually maps that to 400 — see `backend/app/api/errors.py` —
      // but skipping the retry path is still correct: there is nothing
      // to refresh before the very first token pair exists).
      skipAuthHeader: true,
      skipAuthRetry: true,
    );
    return _tokensFromJson(json);
  }

  @override
  Future<AuthTokens> login({required String email, required String password}) async {
    final Map<String, dynamic> json = await _client.post(
      '/login',
      body: <String, dynamic>{'email': email, 'password': password},
      // A wrong-password 401 here is a real, user-correctable failure
      // (`backend/app/api/errors.py`'s own documented policy: `unwrap_
      // or_401` for `LoginHandler`) — not an expired-token 401.
      // Attempting a token refresh in response would be nonsensical
      // (there is no session yet to refresh) and would only delay
      // surfacing the real "wrong email or password" error to the
      // login screen.
      skipAuthHeader: true,
      skipAuthRetry: true,
    );
    return _tokensFromJson(json);
  }

  @override
  Future<AuthTokens> refresh({required String refreshToken}) async {
    final Map<String, dynamic> json = await _client.post(
      '/refresh',
      body: <String, dynamic>{'refresh_token': refreshToken},
      // The refresh token itself is the credential this call carries —
      // never the (possibly already-expired) access token. `skipAuthRetry`
      // is what stops `AuthInterceptor` from trying to "refresh the
      // refresh" on a 401 here, which would recurse forever.
      skipAuthHeader: true,
      skipAuthRetry: true,
    );
    return _tokensFromJson(json);
  }

  @override
  Future<void> logout() async {
    // Requires a valid bearer token (`backend/app/api/routes/auth.py`'s
    // own table: "yes" under Auth required) — no skip flags, so this
    // gets the normal bearer-header/refresh-retry treatment every other
    // authenticated request does.
    await _client.postEmpty('/logout');
  }

  @override
  Future<AuthUser> currentUser() async {
    final Map<String, dynamic> json = await _client.get('/me');
    return AuthUser(
      userId: json['user_id'] as String,
      email: json['email'] as String,
      role: AuthRole.fromWire(json['role'] as String),
      accountStatus: AccountStatus.fromWire(json['account_status'] as String),
      locale: json['locale'] as String,
      timezone: json['timezone'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  /// Shared by [register]/[login]/[refresh] — all three return the
  /// exact same real `TokenResponse` shape
  /// (`backend/app/api/schemas/auth.py`).
  AuthTokens _tokensFromJson(Map<String, dynamic> json) {
    return AuthTokens(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      tokenType: json['token_type'] as String,
      expiresIn: json['expires_in'] as int,
    );
  }
}
