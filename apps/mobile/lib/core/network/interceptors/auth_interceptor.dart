import 'dart:async';

import 'package:dio/dio.dart';

/// Attaches a bearer token to every outgoing request, and — the harder
/// half — implements the automatic-refresh-then-retry flow
/// `docs/adr/0042-production-integration-plan.md` Part 2 planned:
/// a request that comes back 401 triggers exactly one refresh attempt,
/// every other request that fails 401 *while that refresh is already in
/// flight* waits on the same attempt rather than triggering a refresh
/// storm, and a refresh that itself fails calls [onRefreshFailed] (real
/// logout — see `AuthController.logoutFromRefreshFailure` at the call
/// site in `lib/main.dart`) exactly once before letting the original
/// 401 propagate as a real [ApiException] the caller can still see.
///
/// Deliberately takes three plain closures, not a direct dependency on
/// `AuthRepository`/`AuthController` — `lib/core/network/` has no
/// import of `lib/features/auth/` anywhere, and this is why: the
/// network layer is wired *by* the auth layer (`lib/main.dart`
/// constructs this with real callbacks), never the other way around.
/// [ApiClient] itself is agnostic to what "a token" or "a refresh"
/// means; this class only knows it can ask for one and be told whether
/// a retry attempt should happen.
class AuthInterceptor extends Interceptor {
  AuthInterceptor({
    required Dio dio,
    required Future<String?> Function() getAccessToken,
    Future<bool> Function()? refreshToken,
    Future<void> Function()? onRefreshFailed,
  })  : _dio = dio,
        _getAccessToken = getAccessToken,
        _refreshToken = refreshToken,
        _onRefreshFailed = onRefreshFailed;

  final Dio _dio;
  final Future<String?> Function() _getAccessToken;
  final Future<bool> Function()? _refreshToken;
  final Future<void> Function()? _onRefreshFailed;

  /// Non-null exactly while one refresh attempt is in flight — every
  /// 401 that arrives during that window awaits this same [Completer]
  /// instead of calling [_refreshToken] again.
  Completer<bool>? _refreshInFlight;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    // `login`/`register`/`refresh` themselves are issued with
    // `extra['skipAuthHeader'] = true` by `ApiAuthRepository` — there is
    // no access token yet (login/register) or the refresh token, not
    // the access token, is the credential that call carries (refresh),
    // so attaching a possibly-stale bearer header to those three calls
    // specifically would be actively wrong, not merely redundant.
    if (options.extra['skipAuthHeader'] != true) {
      final String? token = await _getAccessToken();
      if (token != null) {
        options.headers['Authorization'] = 'Bearer $token';
      }
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    final bool is401 = err.response?.statusCode == 401;
    // `refresh` and `login`/`register` are marked `skipAuthRetry` for
    // the same reason they skip the request header above: a 401 from
    // `POST /refresh` itself means the refresh token is dead, and
    // attempting to "refresh the refresh" would recurse forever with
    // nothing to break the loop.
    final bool skipRetry = err.requestOptions.extra['skipAuthRetry'] == true;

    if (!is401 || skipRetry || _refreshToken == null) {
      handler.next(err);
      return;
    }

    final bool refreshed = await _attemptRefresh();
    if (!refreshed) {
      if (_onRefreshFailed != null) {
        await _onRefreshFailed();
      }
      handler.next(err);
      return;
    }

    final RequestOptions retryOptions = err.requestOptions;
    final String? newToken = await _getAccessToken();
    if (newToken != null) {
      retryOptions.headers['Authorization'] = 'Bearer $newToken';
    }
    try {
      final Response<dynamic> response = await _dio.fetch<dynamic>(retryOptions);
      handler.resolve(response);
    } on DioException catch (retryError) {
      handler.next(retryError);
    }
  }

  Future<bool> _attemptRefresh() {
    final Completer<bool>? inFlight = _refreshInFlight;
    if (inFlight != null) {
      return inFlight.future;
    }

    final Completer<bool> completer = Completer<bool>();
    _refreshInFlight = completer;
    _refreshToken!().then((bool ok) {
      completer.complete(ok);
      _refreshInFlight = null;
    }).catchError((Object _) {
      completer.complete(false);
      _refreshInFlight = null;
    });
    return completer.future;
  }
}
