import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../application/auth_controller.dart';
import '../domain/auth_models.dart';

/// The real [TokenStorage] — Keychain on iOS, an
/// EncryptedSharedPreferences/Keystore-backed store on Android (both via
/// `flutter_secure_storage`, never plain `shared_preferences`, which
/// stores its values unencrypted). Persists exactly one secret: the
/// refresh token. See [AuthController.currentAccessToken]'s own doc
/// comment for why the access token is never written to disk at all,
/// by any storage mechanism, secure or otherwise.
class SecureTokenStorage implements TokenStorage {
  SecureTokenStorage({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  final FlutterSecureStorage _storage;

  static const String _refreshTokenKey = 'gym_companion.refresh_token';

  @override
  Future<void> saveTokens(AuthTokens tokens) async {
    await _storage.write(key: _refreshTokenKey, value: tokens.refreshToken);
  }

  @override
  Future<String?> readRefreshToken() => _storage.read(key: _refreshTokenKey);

  @override
  Future<void> clear() => _storage.delete(key: _refreshTokenKey);
}
