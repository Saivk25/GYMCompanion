import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import 'api_config.dart';
import 'api_error_mapper.dart';
import 'interceptors/auth_interceptor.dart';
import 'interceptors/logging_interceptor.dart';
import 'interceptors/retry_interceptor.dart';

/// The one HTTP client this app constructs. Every real (`ApiX`-prefixed)
/// repository takes an [ApiClient] in its constructor and calls [get]/
/// [getList]/[post]/[patch]/[delete] — `package:dio` itself is never
/// imported outside `lib/core/network/`, so a future client-library swap
/// (unlikely, but real interfaces exist precisely so this stays
/// possible) would touch this one file, not every repository.
///
/// Per `docs/adr/0042-production-integration-plan.md` Part 2, this is
/// Step 1 of the production integration work: the networking layer
/// exists and is fully independent of authentication (see
/// [accessTokenProvider]/[refreshToken]/[onRefreshFailed] below — all
/// optional, all plain closures) so it can be built, tested, and
/// committed before the Auth module that will supply real callbacks for
/// them exists at all (Step 2).
class ApiClient {
  ApiClient({
    Dio? dio,
    String? baseUrl,
    Future<String?> Function()? accessTokenProvider,
    Future<bool> Function()? refreshToken,
    Future<void> Function()? onRefreshFailed,
  }) : _dio = dio ??
            Dio(
              BaseOptions(
                baseUrl: baseUrl ?? ApiConfig.baseUrl,
                connectTimeout: ApiConfig.connectTimeout,
                receiveTimeout: ApiConfig.receiveTimeout,
                sendTimeout: ApiConfig.sendTimeout,
                headers: const <String, String>{'Content-Type': 'application/json'},
              ),
            ) {
    if (accessTokenProvider != null) {
      _dio.interceptors.add(
        AuthInterceptor(
          dio: _dio,
          getAccessToken: accessTokenProvider,
          refreshToken: refreshToken,
          onRefreshFailed: onRefreshFailed,
        ),
      );
    }
    // Retry before logging: a retried request's own log lines should
    // still appear (each `_dio.fetch` re-enters the interceptor chain
    // from the top), so ordering here doesn't hide retry attempts from
    // the debug log — it only decides which interceptor sees a failure
    // first, and retry needs to see it before logging would otherwise
    // log the same failure twice for one logical request.
    _dio.interceptors.add(RetryInterceptor(dio: _dio));
    if (kDebugMode) {
      _dio.interceptors.add(ApiLoggingInterceptor());
    }
  }

  final Dio _dio;

  /// A GET expected to return a single JSON object.
  Future<Map<String, dynamic>> get(String path, {Map<String, dynamic>? queryParameters}) async {
    final dynamic data = await _sendRaw(
      () => _dio.get<dynamic>(path, queryParameters: queryParameters),
    );
    return data as Map<String, dynamic>;
  }

  /// A GET expected to return a JSON array — every list endpoint this
  /// backend exposes (`backend/app/api/routes/v1/*.py`'s own `list[...]`
  /// response models) returns the full collection with no pagination
  /// envelope (see ADR 0042 Part 2's own "no pagination exists anywhere"
  /// finding), so this returns the decoded array directly rather than
  /// unwrapping a `results`/`items` field that does not exist.
  Future<List<dynamic>> getList(String path, {Map<String, dynamic>? queryParameters}) async {
    final dynamic data = await _sendRaw(
      () => _dio.get<dynamic>(path, queryParameters: queryParameters),
    );
    return data as List<dynamic>;
  }

  /// [skipAuthHeader]/[skipAuthRetry] exist for exactly three call
  /// sites in this whole app (`ApiAuthRepository.login`/`.register`/
  /// `.refresh`) — see [AuthInterceptor]'s own doc comment for why those
  /// three, and only those three, opt out of the default bearer-header
  /// and refresh-retry behavior every other request gets automatically.
  Future<Map<String, dynamic>> post(
    String path, {
    Object? body,
    bool skipAuthHeader = false,
    bool skipAuthRetry = false,
  }) async {
    final dynamic data = await _sendRaw(
      () => _dio.post<dynamic>(
        path,
        data: body,
        options: (skipAuthHeader || skipAuthRetry)
            ? Options(
                extra: <String, dynamic>{
                  if (skipAuthHeader) 'skipAuthHeader': true,
                  if (skipAuthRetry) 'skipAuthRetry': true,
                },
              )
            : null,
      ),
    );
    return data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> patch(String path, {Object? body}) async {
    final dynamic data = await _sendRaw(() => _dio.patch<dynamic>(path, data: body));
    return data as Map<String, dynamic>;
  }

  /// This backend has no endpoint that returns a body on delete/cancel-
  /// style actions with a `204`/action response — several return
  /// `IdResponse` instead (see `backend/app/api/schemas/common.py`) — so
  /// [delete] returns nothing; a repository calling an action endpoint
  /// that *does* return a body should use [post]/[patch] instead.
  Future<void> delete(String path) async {
    await _sendRaw(() => _dio.delete<dynamic>(path));
  }

  Future<dynamic> _sendRaw(Future<Response<dynamic>> Function() request) async {
    try {
      final Response<dynamic> response = await request();
      return response.data;
    } on DioException catch (error) {
      throw ApiErrorMapper.map(error);
    }
  }
}
