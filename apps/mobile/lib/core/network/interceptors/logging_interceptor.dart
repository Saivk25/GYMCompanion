import 'dart:developer' as developer;

import 'package:dio/dio.dart';

/// Request/response/error logging for local development only — never
/// added to the [Dio] instance's interceptor chain at all when
/// `kDebugMode` is `false` (see `ApiClient`'s own constructor, the one
/// place that check happens), so this class has zero cost and zero
/// output in a release build rather than a runtime check on every call.
///
/// Uses `dart:developer`'s [developer.log], not `print` — this
/// project's own lint config (`analysis_options.yaml`) enables
/// `avoid_print` specifically so a debug `print` never survives into
/// production code by accident; `developer.log` is the one channel a
/// production build can still compile with a logging call left in,
/// since it is a no-op outside an attached debugger/DevTools session
/// rather than writing to stdout unconditionally.
class ApiLoggingInterceptor extends Interceptor {
  static const String _name = 'ApiClient';

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    developer.log('--> ${options.method} ${options.uri}', name: _name);
    handler.next(options);
  }

  @override
  void onResponse(Response<dynamic> response, ResponseInterceptorHandler handler) {
    developer.log(
      '<-- ${response.statusCode} ${response.requestOptions.method} ${response.requestOptions.uri}',
      name: _name,
    );
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    developer.log(
      '<-- ERROR ${err.response?.statusCode} ${err.requestOptions.method} '
      '${err.requestOptions.uri}: ${err.message}',
      name: _name,
      level: 900, // warning
    );
    handler.next(err);
  }
}
