import 'package:dio/dio.dart';

import '../api_config.dart';

/// Retries a request exactly once policy line from
/// `docs/adr/0042-production-integration-plan.md` Part 2 makes real:
/// **only GET requests, only on a network-level failure** (connection
/// error or timeout — never on a real backend response, 4xx or 5xx
/// alike, since those are the backend genuinely answering, not a
/// transient failure to retry past).
///
/// GET-only is not a stylistic choice — it is the one method this
/// backend's own API is safe to retry blindly. `backend/app/api/
/// errors.py`'s own documented failure taxonomy has no idempotency-key
/// concept anywhere (confirmed during the ADR 0042 audit: no
/// idempotency-key header, no dedup mechanism exists in this API), so
/// automatically retrying a POST/PATCH/DELETE that *did* reach the
/// server but whose response was lost to a network blip risks a real
/// double-mutation (e.g. two meals logged from one tap) with nothing on
/// either end to detect or prevent it. A GET is safe to retry
/// unconditionally — reading twice has no side effect — which is
/// exactly why this interceptor checks the method before anything else.
class RetryInterceptor extends Interceptor {
  RetryInterceptor({required Dio dio, this.maxRetries = ApiConfig.maxRetries}) : _dio = dio;

  final Dio _dio;
  final int maxRetries;

  static const String _retryCountKey = 'retryCount';

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    final bool isRetryableFailure = err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.sendTimeout ||
        err.type == DioExceptionType.receiveTimeout ||
        err.type == DioExceptionType.connectionError;
    final bool isIdempotent = err.requestOptions.method.toUpperCase() == 'GET';

    if (!isRetryableFailure || !isIdempotent) {
      handler.next(err);
      return;
    }

    final int attempt = (err.requestOptions.extra[_retryCountKey] as int?) ?? 0;
    if (attempt >= maxRetries) {
      handler.next(err);
      return;
    }

    // A short, increasing delay rather than an immediate retry — a
    // connection error that's about to happen again in the next 10ms
    // benefits from letting the underlying condition (a flaky Wi-Fi
    // handoff, a momentarily saturated connection) actually pass.
    await Future<void>.delayed(Duration(milliseconds: 300 * (attempt + 1)));

    final RequestOptions retryOptions = err.requestOptions;
    retryOptions.extra[_retryCountKey] = attempt + 1;

    try {
      final Response<dynamic> response = await _dio.fetch<dynamic>(retryOptions);
      handler.resolve(response);
    } on DioException catch (retryError) {
      handler.next(retryError);
    }
  }
}
