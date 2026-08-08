/// The real, backend-verified shapes Auth is built on. Every field here
/// mirrors a real response schema in `backend/app/api/schemas/auth.py` —
/// nothing on this page is invented; a field this app doesn't yet use
/// (e.g. [AuthUser.createdAt]) is still modeled faithfully rather than
/// dropped, so a DTO mapping never has to silently discard real backend
/// data.
library;

/// Mirrors `backend/app/domain/auth/enums.py`'s `Role` — a single
/// active member today (`MEMBER = "member"`), deliberately modeled as a
/// real enum rather than a bare `String` so a second role the backend
/// adds later is a compile-time-visible gap here, not a silently-
/// accepted string.
enum AuthRole {
  member;

  static AuthRole fromWire(String value) => switch (value) {
        'member' => AuthRole.member,
        _ => throw ArgumentError('Unknown AuthRole from backend: "$value"'),
      };
}

/// Mirrors `backend/app/domain/user/enums.py`'s `AccountStatus` — the
/// User aggregate's real lifecycle (Invited -> Active -> Suspended ->
/// Deleted -> Purged), not a client-invented simplification of it.
enum AccountStatus {
  invited,
  active,
  suspended,
  deleted,
  purged;

  static AccountStatus fromWire(String value) => switch (value) {
        'invited' => AccountStatus.invited,
        'active' => AccountStatus.active,
        'suspended' => AccountStatus.suspended,
        'deleted' => AccountStatus.deleted,
        'purged' => AccountStatus.purged,
        _ => throw ArgumentError('Unknown AccountStatus from backend: "$value"'),
      };
}

/// Mirrors `TokenResponse` (`backend/app/api/schemas/auth.py`) — the
/// body every one of `POST /register`/`/login`/`/refresh` returns.
class AuthTokens {
  const AuthTokens({
    required this.accessToken,
    required this.refreshToken,
    required this.tokenType,
    required this.expiresIn,
  });

  final String accessToken;
  final String refreshToken;
  final String tokenType;

  /// Access token lifetime in seconds, per the backend's own field
  /// description — `backend/app/core/config.py`'s real default is 15
  /// minutes (900s), consumed here only for a future "refresh
  /// proactively before expiry" optimization, not required for
  /// correctness: the reactive 401-triggers-refresh flow
  /// (`AuthInterceptor`) works regardless of whether this value is ever
  /// read.
  final int expiresIn;
}

/// Mirrors `CurrentUserResponse` (`backend/app/api/schemas/auth.py`) —
/// the body `GET /me` returns, and the shape [AuthController] holds
/// once a session is established.
class AuthUser {
  const AuthUser({
    required this.userId,
    required this.email,
    required this.role,
    required this.accountStatus,
    required this.locale,
    required this.timezone,
    required this.createdAt,
  });

  final String userId;
  final String email;
  final AuthRole role;
  final AccountStatus accountStatus;
  final String locale;
  final String timezone;
  final DateTime createdAt;
}

/// The one thing every screen in this app actually needs to know:
/// whether there is a signed-in user right now, and if so, who. Modeled
/// as a closed set of three states — never a bare `AuthUser?` — because
/// "we haven't checked yet" (app just launched, a stored refresh token
/// is still being validated) and "we checked, and there is no session"
/// are genuinely different states a router guard must tell apart: the
/// first should show a loading screen, never a redirect; the second
/// should redirect to Login.
sealed class AuthState {
  const AuthState();
}

class AuthInitial extends AuthState {
  const AuthInitial();
}

class AuthAuthenticated extends AuthState {
  const AuthAuthenticated(this.user);

  final AuthUser user;
}

class AuthUnauthenticated extends AuthState {
  const AuthUnauthenticated();
}
