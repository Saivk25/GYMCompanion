import 'package:dio/dio.dart';

import 'api_exception.dart';

/// Translates a [DioException] into this app's own [ApiException] — the
/// one place either type is named outside `lib/core/network/` itself.
/// Every real repository's catch block calls [ApiErrorMapper.map] and
/// rethrows the result; nothing else in this app imports `package:dio`.
abstract final class ApiErrorMapper {
  static ApiException map(DioException error) {
    if (_isNetworkFailureType(error.type)) {
      return ApiException(
        statusCode: null,
        message: _networkMessage(error.type),
        isNetworkError: true,
      );
    }

    final Response<dynamic>? response = error.response;
    if (response == null) {
      // `DioExceptionType.unknown` etc. with genuinely no response —
      // still a network-shaped failure from this app's point of view,
      // even though it isn't one of Dio's own named timeout/connection
      // error types.
      return ApiException(
        statusCode: null,
        message: error.message ?? 'A network error occurred.',
        isNetworkError: true,
      );
    }

    return ApiException(
      statusCode: response.statusCode,
      message: _extractDetail(response.data) ??
          'Request failed with status ${response.statusCode}.',
    );
  }

  static bool _isNetworkFailureType(DioExceptionType type) {
    return type == DioExceptionType.connectionTimeout ||
        type == DioExceptionType.sendTimeout ||
        type == DioExceptionType.receiveTimeout ||
        type == DioExceptionType.connectionError;
  }

  static String _networkMessage(DioExceptionType type) {
    return switch (type) {
      DioExceptionType.connectionTimeout ||
      DioExceptionType.sendTimeout ||
      DioExceptionType.receiveTimeout =>
        'The request timed out. Check your connection and try again.',
      DioExceptionType.connectionError =>
        'Could not reach the server. Check your connection and try again.',
      _ => 'A network error occurred.',
    };
  }

  /// The backend's `ErrorResponse.detail` (`backend/app/api/schemas/
  /// common.py`) is `str | list[str]` on the wire — every failure path
  /// in that API (`RequestValidationError`, `DomainInvariantViolationError`,
  /// an `ApplicationResult.fail(...)`, an unhandled exception) produces
  /// this same envelope, so this is the one place either shape needs
  /// unwrapping into a single display string.
  static String? _extractDetail(dynamic data) {
    if (data is Map<String, dynamic>) {
      final dynamic detail = data['detail'];
      if (detail is String) return detail;
      if (detail is List) return detail.join('; ');
    }
    return null;
  }
}
